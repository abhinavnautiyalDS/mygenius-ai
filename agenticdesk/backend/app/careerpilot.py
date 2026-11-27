"""CareerPilot multi-agent workflow graph.

The graph provides a real fan-out/fan-in execution foundation. External job
providers are intentionally adapters: unconfigured providers return explicit
skipped results instead of fabricated vacancies.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger("agenticdesk.careerpilot")

def _merge_events(left: list[dict[str, Any]] | None, right: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return (left or []) + (right or [])


def _merge_agent_events(
    left: dict[str, dict[str, Any]] | None,
    right: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


def _merge_errors(left: list[str] | None, right: list[str] | None) -> list[str]:
    return (left or []) + (right or [])


def _merge_artifacts(left: dict[str, Any] | None, right: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


AGENTS = (
    "job_discovery",
    "resume_intelligence",
    "company_research",
    "skill_gap_analysis",
    "job_matching",
    "resume_optimization",
    "outreach_drafting",
    "interview_preparation",
)

class CareerState(TypedDict, total=False):
    run_id: str
    task: str
    options: dict[str, bool]
    plan: dict[str, Any]
    events: Annotated[list[dict[str, Any]], _merge_events]
    agent_events: Annotated[dict[str, dict[str, Any]], _merge_agent_events]
    profile: dict[str, Any]
    jobs: list[dict[str, Any]]
    research: list[dict[str, Any]]
    skill_gaps: list[str]
    matches: list[dict[str, Any]]
    artifacts: Annotated[dict[str, Any], _merge_artifacts]
    errors: Annotated[list[str], _merge_errors]
    status: str
    result: str


def _event(agent: str, status: str, detail: str = "") -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "agent": agent,
        "status": status,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _call_model(model_call, system: str, user: str, max_tokens: int = 700) -> str:
    return await model_call([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], max_tokens=max_tokens)


def build_career_graph(model_call, web_search_call=None, profile_loader=None):
    """Build a compiled graph with parallel research and dependent stages.

    model_call and providers are injected from the existing AgenticDesk service,
    so Dhir remains the reasoning model and no new model endpoint is required.
    """

    async def orchestrator(state: CareerState) -> dict[str, Any]:
        prompt = (
            "Convert the user's career/job-search goal into concise JSON with keys "
            "job_titles (array), locations (array), salary_min_lpa (number or null), "
            "salary_max_lpa (number or null), experience (string), skills (array), "
            "and constraints (array). Do not invent profile information. "
            "Return JSON only."
        )
        raw = await _call_model(model_call, prompt, state["task"], 450)
        try:
            plan = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
            if not isinstance(plan, dict):
                raise ValueError("Planner output must be an object")
        except (ValueError, TypeError, json.JSONDecodeError):
            # Avoid losing user-provided constraints when the 2B model returns
            # prose instead of JSON. This parser only extracts explicit fields.
            plan = {
                "job_titles": [],
                "locations": [],
                "salary_min_lpa": None,
                "salary_max_lpa": None,
                "experience": "",
                "skills": [],
                "constraints": [],
                "raw_goal": state["task"],
                "planner_note": "Structured planning unavailable; original goal preserved.",
            }
            goal = state["task"]
            role_match = re.search(r"(?:roles?|positions?|jobs?)\s*(?:as|for|:)?\s*([A-Za-z0-9 +#/,&-]+?)(?:\s+in\s+|,|with\s+a\s+salary|$)", goal, re.IGNORECASE)
            location_match = re.search(r"\bin\s+([A-Za-z][A-Za-z0-9 ,&-]+?)(?:\s+with\s+a\s+salary|\s+at\s+|$)", goal, re.IGNORECASE)
            salary_match = re.search(r"(?:₹|INR\s*)?\s*(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*LPA", goal, re.IGNORECASE)
            if role_match:
                plan["job_titles"] = [part.strip() for part in re.split(r",|\band\b", role_match.group(1), flags=re.IGNORECASE) if part.strip()]
            if location_match:
                plan["locations"] = [part.strip() for part in location_match.group(1).split(",") if part.strip()]
            if salary_match:
                plan["salary_min_lpa"] = float(salary_match.group(1))
                plan["salary_max_lpa"] = float(salary_match.group(2))

        profile = (await profile_loader()) if profile_loader is not None else {}
        profile = profile if isinstance(profile, dict) else {}
        for key, profile_key in (
            ("job_titles", "preferred_roles"),
            ("locations", "preferred_locations"),
            ("salary_min_lpa", "salary_min_lpa"),
            ("salary_max_lpa", "salary_max_lpa"),
            ("skills", "skills"),
        ):
            value = profile.get(profile_key)
            if value not in (None, "", []):
                if plan.get(key) in (None, "", []):
                    plan[key] = value

        event = _event("orchestrator", "completed", "Created plan and loaded candidate preferences")
        return {
            "plan": plan,
            "profile": profile if profile else {"status": "missing", "skills": [], "experience": [], "projects": []},
            "status": "running",
            "events": [event],
            "agent_events": {"orchestrator": event},
            "errors": [],
        }

    async def job_discovery(state: CareerState) -> dict[str, Any]:
        if not state.get("options", {}).get("web_search", False) or web_search_call is None:
            event = _event("job_discovery", "skipped", "Web search disabled or provider unavailable")
            return {"jobs": [], "events": [event], "agent_events": {"job_discovery": event}}

        plan = state.get("plan", {})
        terms = plan.get("job_titles") or [state["task"]]
        locations = plan.get("locations") or []
        queries = [f'{title} jobs {" ".join(locations)} India' for title in terms[:5]]
        try:
            batches = await asyncio.gather(*(web_search_call(query) for query in queries))
            results: list[dict[str, Any]] = []
            for batch in batches:
                for item in batch or []:
                    url = str(item.get("url", "")).strip()
                    title = str(item.get("title", "")).strip()
                    if not url or not title:
                        continue
                    results.append({
                        "title": title[:300],
                        "url": url[:2000],
                        "snippet": str(item.get("content", ""))[:1200],
                        "source": "web_search",
                        "listing_verified": False,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    })
            unique = {item["url"]: item for item in results}
            event = _event("job_discovery", "completed", f"Collected {len(unique)} web leads; vacancy status not verified")
            return {"jobs": list(unique.values())[:40], "events": [event], "agent_events": {"job_discovery": event}}
        except Exception as exc:
            logger.exception("CareerPilot job discovery failed")
            event = _event("job_discovery", "failed", "Search provider request failed")
            return {
                "jobs": [],
                "errors": [f"job_discovery: {type(exc).__name__}"],
                "events": [event],
                "agent_events": {"job_discovery": event},
            }

    async def resume_intelligence(state: CareerState) -> dict[str, Any]:
        profile = state.get("profile", {})
        if not profile or profile.get("status") == "missing":
            event = _event("resume_intelligence", "needs_input", "Complete the candidate profile or upload a resume")
            empty_profile = {"status": "missing", "skills": [], "experience": [], "projects": []}
            return {"profile": empty_profile, "events": [event], "agent_events": {"resume_intelligence": event}}
        event = _event("resume_intelligence", "completed", "Loaded candidate profile")
        return {"profile": profile, "events": [event], "agent_events": {"resume_intelligence": event}}

    async def company_research(state: CareerState) -> dict[str, Any]:
        # Company-specific research is intentionally marked unavailable until
        # a separate source provider is connected.
        event = _event("company_research", "skipped", "No company research provider configured yet")
        return {"research": [], "events": [event], "agent_events": {"company_research": event}}

    async def skill_gap_analysis(state: CareerState) -> dict[str, Any]:
        desired = {str(value).casefold() for value in state.get("plan", {}).get("skills", [])}
        existing = {str(value).casefold() for value in state.get("profile", {}).get("skills", [])}
        gaps = sorted(desired - existing) if existing else []
        status = "completed" if existing else "needs_input"
        detail = f"Identified {len(gaps)} potential skill gaps" if existing else "Candidate profile is not available"
        event = _event("skill_gap_analysis", status, detail)
        return {"skill_gaps": gaps, "events": [event], "agent_events": {"skill_gap_analysis": event}}

    async def job_matching(state: CareerState) -> dict[str, Any]:
        jobs = state.get("jobs", [])
        profile = state.get("profile", {})
        if not jobs or profile.get("status") == "missing":
            event = _event("job_matching", "needs_input", "Requires discovered job leads and a candidate profile")
            return {"matches": [], "events": [event], "agent_events": {"job_matching": event}}
        skills = {str(value).casefold() for value in profile.get("skills", [])}
        ranked: list[dict[str, Any]] = []
        for job in jobs:
            searchable = f'{job.get("title", "")} {job.get("snippet", "")}'.casefold()
            overlap = sum(1 for skill in skills if skill and skill in searchable)
            ranked.append({**job, "matched_skill_mentions": overlap})
        ranked.sort(key=lambda item: item["matched_skill_mentions"], reverse=True)
        event = _event("job_matching", "completed", f"Ranked {len(ranked[:20])} job leads by skill mentions")
        return {"matches": ranked[:20], "events": [event], "agent_events": {"job_matching": event}}

    async def resume_optimization(state: CareerState) -> dict[str, Any]:
        payload = {
            "candidate_profile": state.get("profile", {}),
            "job_matches": state.get("matches", [])[:5],
            "goal": state.get("plan", {}),
        }
        prompt = (
            "Act as a resume optimization specialist. Tailor resume guidance to the "
            "supplied role and candidate profile. Never invent skills, employers, "
            "dates, qualifications, metrics or achievements. Mark missing details "
            "as placeholders. Return concise JSON with resume_guidance and "
            "role_specific_keywords."
        )
        try:
            raw = await _call_model(model_call, prompt, json.dumps(payload, ensure_ascii=False), 750)
            event = _event("resume_optimization", "completed", "Generated role-focused resume guidance for review")
            return {"artifacts": {"resume_guidance": raw}, "events": [event], "agent_events": {"resume_optimization": event}}
        except Exception as exc:
            logger.exception("CareerPilot resume optimization failed")
            event = _event("resume_optimization", "failed", "Could not generate resume guidance")
            return {"errors": [f"resume_optimization: {type(exc).__name__}"], "events": [event], "agent_events": {"resume_optimization": event}}

    async def outreach_drafting(state: CareerState) -> dict[str, Any]:
        payload = {
            "candidate_profile": state.get("profile", {}),
            "job_matches": state.get("matches", [])[:5],
            "goal": state.get("plan", {}),
        }
        prompt = (
            "Act as a recruiter outreach specialist. Draft concise, personalized "
            "recruiter messages and cover letters using only supplied candidate "
            "facts and job information. Do not invent contact names, experience "
            "or achievements. Return JSON with cover_letter_drafts and "
            "recruiter_message_drafts. Draft only; do not send anything."
        )
        try:
            raw = await _call_model(model_call, prompt, json.dumps(payload, ensure_ascii=False), 750)
            event = _event("outreach_drafting", "completed", "Generated recruiter outreach drafts for review")
            return {"artifacts": {"outreach_drafts": raw}, "events": [event], "agent_events": {"outreach_drafting": event}}
        except Exception as exc:
            logger.exception("CareerPilot outreach drafting failed")
            event = _event("outreach_drafting", "failed", "Could not generate outreach drafts")
            return {"errors": [f"outreach_drafting: {type(exc).__name__}"], "events": [event], "agent_events": {"outreach_drafting": event}}

    async def interview_preparation(state: CareerState) -> dict[str, Any]:
        matches = state.get("matches", [])
        if not matches:
            event = _event("interview_preparation", "needs_input", "Select a suitable job before role-specific interview preparation")
            return {"events": [event], "agent_events": {"interview_preparation": event}}
        payload = {"job_matches": matches[:3], "candidate_profile": state.get("profile", {})}
        prompt = (
            "Act as an interview preparation coach. Create likely role-relevant "
            "interview topics and practice questions from the supplied job lead "
            "and candidate profile. Distinguish inferred questions from confirmed "
            "company interview questions. Return concise JSON."
        )
        try:
            raw = await _call_model(model_call, prompt, json.dumps(payload, ensure_ascii=False), 750)
            event = _event("interview_preparation", "completed", "Generated practice questions, not confirmed company questions")
            return {"artifacts": {"interview_preparation": raw}, "events": [event], "agent_events": {"interview_preparation": event}}
        except Exception as exc:
            logger.exception("CareerPilot interview preparation failed")
            event = _event("interview_preparation", "failed", "Could not generate interview preparation")
            return {"errors": [f"interview_preparation: {type(exc).__name__}"], "events": [event], "agent_events": {"interview_preparation": event}}

    async def finalize(state: CareerState) -> dict[str, Any]:
        summary = {
            "plan": state.get("plan", {}),
            "profile_status": state.get("profile", {}).get("status", "available"),
            "job_leads_discovered": len(state.get("jobs", [])),
            "matches_prepared": len(state.get("matches", [])),
            "skill_gaps": state.get("skill_gaps", []),
            "artifacts": state.get("artifacts", {}),
            "requires_user_review": True,
            "errors": state.get("errors", []),
            "execution_note": (
                "No application was submitted and no recruiter message was sent. "
                "General web search results are leads, not verified vacancies. "
                "Review all generated drafts before using them."
            ),
        }
        event = _event("orchestrator", "completed", "Merged agent outputs")
        return {
            "result": json.dumps(summary, ensure_ascii=False, indent=2),
            "status": "completed_with_warnings" if state.get("errors") else "completed",
            "events": [event],
            "agent_events": {"orchestrator": event},
        }

    graph = StateGraph(CareerState)
    graph.add_node("orchestrator", orchestrator)
    graph.add_node("job_discovery", job_discovery)
    graph.add_node("resume_intelligence", resume_intelligence)
    graph.add_node("company_research", company_research)
    graph.add_node("skill_gap_analysis", skill_gap_analysis)
    graph.add_node("job_matching", job_matching)
    graph.add_node("resume_optimization", resume_optimization)
    graph.add_node("outreach_drafting", outreach_drafting)
    graph.add_node("interview_preparation", interview_preparation)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "orchestrator")
    # LangGraph executes these sibling nodes in parallel and joins before the
    # dependent analysis/matching stage.
    graph.add_edge("orchestrator", "job_discovery")
    graph.add_edge("orchestrator", "resume_intelligence")
    graph.add_edge("orchestrator", "company_research")
    graph.add_edge("resume_intelligence", "skill_gap_analysis")
    graph.add_edge(["job_discovery", "skill_gap_analysis", "company_research"], "job_matching")
    graph.add_edge("job_matching", "resume_optimization")
    graph.add_edge("job_matching", "outreach_drafting")
    graph.add_edge("job_matching", "interview_preparation")
    graph.add_edge(["resume_optimization", "outreach_drafting", "interview_preparation"], "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


async def run_career_workflow(
    task: str,
    *,
    model_call,
    web_search_call=None,
    profile_loader=None,
    web_search: bool = False,
) -> dict[str, Any]:
    """Execute one graph run and return inspectable agent events and artifacts."""
    graph = build_career_graph(model_call, web_search_call, profile_loader)
    initial: CareerState = {
        "run_id": str(uuid.uuid4()),
        "task": task,
        "options": {"web_search": web_search},
        "status": "queued",
        "events": [],
        "agent_events": {},
        "errors": [],
    }
    final = await graph.ainvoke(initial)
    return {
        "run_id": final.get("run_id", initial["run_id"]),
        "status": final.get("status", "completed"),
        "result": final.get("result", ""),
        "events": sorted(final.get("events", []), key=lambda e: e.get("timestamp", "")),
        "agent_count": len(AGENTS),
        "agents": {**final.get("agent_events", {})},
    }
