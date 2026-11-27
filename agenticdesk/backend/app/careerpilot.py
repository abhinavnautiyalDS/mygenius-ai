"""CareerPilot multi-agent workflow graph.

The graph provides a real fan-out/fan-in execution foundation. External job
providers are intentionally adapters: unconfigured providers return explicit
skipped results instead of fabricated vacancies.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger("agenticdesk.careerpilot")

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
    events: list[dict[str, Any]]
    agent_events: dict[str, dict[str, Any]]
    profile: dict[str, Any]
    jobs: list[dict[str, Any]]
    research: list[dict[str, Any]]
    skill_gaps: list[str]
    matches: list[dict[str, Any]]
    artifacts: dict[str, Any]
    errors: list[str]
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
            # Conservative fallback: retain the user instruction and do not
            # guess salary, experience, or qualifications.
            plan = {
                "job_titles": [],
                "locations": [],
                "salary_min_lpa": None,
                "salary_max_lpa": None,
                "experience": "",
                "skills": [],
                "constraints": [],
                "raw_goal": state["task"],
                "planner_note": "Could not parse structured plan; preserved original goal.",
            }
        profile = (await profile_loader()) if profile_loader is not None else {}
        if not isinstance(profile, dict):
            profile = {}
        # The saved candidate profile is the source of truth for preferences;
        # natural-language constraints from this task take precedence.
        for key in ("job_titles", "locations", "salary_min_lpa", "salary_max_lpa", "skills"):
            profile_key = {
                "job_titles": "preferred_roles",
                "locations": "preferred_locations",
            }.get(key, key)
            value = profile.get(profile_key)
            if value not in (None, "", []):
                if key not in plan or plan.get(key) in (None, "", []):
                    plan[key] = value
        return {
            "plan": plan,
            "profile": profile if profile else {"status": "missing", "skills": [], "experience": [], "projects": []},
            "status": "running",
            "events": [_event("orchestrator", "completed", "Created task plan and loaded profile preferences")],
            "agent_events": {"orchestrator": _event("orchestrator", "completed", "Created task plan and loaded profile preferences")},
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
            batches = await asyncio.gather(*(web_search_call(q) for q in queries))
            results: list[dict[str, Any]] = []
            for batch in batches:
                for item in batch or []:
                    url = str(item.get("url", "")).strip()
                    title = str(item.get("title", "")).strip()
                    if url and title:
                        results.append({
                            "title": title[:300],
                            "url": url[:2000],
                            "snippet": str(item.get("content", ""))[:1200],
                            "source": "web_search",
                            "verified_at": datetime.now(timezone.utc).isoformat(),
                        })
            unique = {item["url"]: item for item in results}
            event = _event("job_discovery", "completed", f"Collected {len(unique)} web results; listings require verification")
            return {"jobs": list(unique.values())[:40], "events": [event], "agent_events": {"job_discovery": event}}
        except Exception as exc:
            logger.exception("CareerPilot job discovery failed")
            return {
                "jobs": [],
                "errors": [f"job_discovery: {type(exc).__name__}"],
                "events": [_event("job_discovery", "failed", "Search provider request failed")],
                "agent_events": {"job_discovery": _event("job_discovery", "failed", "Search provider request failed")},
            }

    async def resume_intelligence(state: CareerState) -> dict[str, Any]:
        profile = state.get("profile", {})
        if not profile or profile.get("status") == "missing":
            return {
                "profile": {"status": "missing", "skills": [], "experience": [], "projects": []},
                "events": [_event("resume_intelligence", "needs_input", "Complete the candidate profile or upload a resume")],
                "agent_events": {"resume_intelligence": _event("resume_intelligence", "needs_input", "Complete the candidate profile or upload a resume")},
            }
        return {
            "profile": profile,
            "events": [_event("resume_intelligence", "completed", "Loaded candidate profile")],
            "agent_events": {"resume_intelligence": _event("resume_intelligence", "completed", "Loaded candidate profile")},
        }

    async def company_research(state: CareerState) -> dict[str, Any]:
        # This node is independent and can later call approved company-data tools.
        # It never invents employer facts in the absence of sources.
        event = _event("company_research", "skipped", "No company research provider configured yet")
        return {"research": [], "events": [event], "agent_events": {"company_research": event}}

    async def skill_gap_analysis(state: CareerState) -> dict[str, Any]:
        plan_skills = {str(x).casefold() for x in state.get("plan", {}).get("skills", [])}
        profile_skills = {str(x).casefold() for x in state.get("profile", {}).get("skills", [])}
        gaps = sorted(plan_skills - profile_skills) if profile_skills else []
        event = _event("skill_gap_analysis", "completed" if profile_skills else "needs_input", f"Identified {len(gaps)} potential skill gaps" if profile_skills else "Candidate profile is not available")
        return {"skill_gaps": gaps, "events": [event], "agent_events": {"skill_gap_analysis": event}}

    async def job_matching(state: CareerState) -> dict[str, Any]:
        jobs = state.get("jobs", [])
        profile = state.get("profile", {})
        if not jobs or profile.get("status") == "missing":
            return {
                "matches": [],
                "events": [_event("job_matching", "needs_input", "Requires discovered listings and a candidate profile")],
                "agent_events": {"job_matching": _event("job_matching", "needs_input", "Requires discovered listings and a candidate profile")},
            }
        # Initial conservative lexical signal only. Do not present this as an
        # ML relevance score; a proper reranker can be added after evaluation.
        skills = {str(x).casefold() for x in profile.get("skills", [])}
        scored = []
        for job in jobs:
            text = (job.get("title", "") + " " + job.get("snippet", "")).casefold()
            overlap = sum(1 for skill in skills if skill and skill in text)
            scored.append({**job, "matched_skill_mentions": overlap})
        scored.sort(key=lambda x: x["matched_skill_mentions"], reverse=True)
        return {
            "matches": scored[:20],
            "events": [_event("job_matching", "completed", f"Ranked {len(scored[:20])} candidate listings by skill mentions")],
            "agent_events": {"job_matching": _event("job_matching", "completed", f"Ranked {len(scored[:20])} candidate listings by skill mentions")},
        }

    async def preparation(state: CareerState) -> dict[str, Any]:
        # Preparation drafts are not application submissions. The model is told
        # never to fabricate employment, achievements, qualifications or skills.
        matches = state.get("matches", [])
        plan = state.get("plan", {})
        profile = state.get("profile", {})
        prompt = (
            "You are a career document preparation assistant. Use only the supplied "
            "candidate facts and job information. Never invent employers, dates, "
            "degrees, skills, achievements, metrics or experience. Clearly mark "
            "missing facts as questions/placeholders. Return concise JSON with "
            "resume_guidance, cover_letter_drafts and recruiter_message_drafts."
        )
        payload = {
            "candidate_profile": profile,
            "job_matches": matches[:5],
            "goal": plan,
        }
        try:
            raw = await _call_model(model_call, prompt, json.dumps(payload, ensure_ascii=False), 1100)
            artifacts = {"preparation_draft": raw, "requires_user_review": True}
            event = _event("resume_optimization", "completed", "Generated review-only preparation draft")
            outreach_event = _event("outreach_drafting", "completed", "Outreach drafts included for review")
            interview_event = _event("interview_preparation", "skipped", "Interview prep will run after a role is selected")
            return {"artifacts": artifacts, "events": [event, outreach_event, interview_event], "agent_events": {\n                "resume_optimization": event, "outreach_drafting": outreach_event, "interview_preparation": interview_event}}
        except Exception as exc:
            logger.exception("CareerPilot preparation failed")
            return {
                "artifacts": {},
                "errors": [f"preparation: {type(exc).__name__}"],
                "events": [_event("resume_optimization", "failed", "Could not prepare drafts")],
                "agent_events": {"resume_optimization": _event("resume_optimization", "failed", "Could not prepare drafts")},
            }

    async def finalize(state: CareerState) -> dict[str, Any]:
        summary = {
            "plan": state.get("plan", {}),
            "profile_status": state.get("profile", {}).get("status", "unknown"),
            "jobs_discovered": len(state.get("jobs", [])),
            "matches_prepared": len(state.get("matches", [])),
            "skill_gaps": state.get("skill_gaps", []),
            "artifacts": state.get("artifacts", {}),
            "errors": state.get("errors", []),
            "execution_note": (
                "This run does not submit job applications or send messages. "
                "Listings from general web search are leads, not verified vacancies. "
                "Use supported employer/ATS sources and obtain approval before external actions."
            ),
        }
        return {
            "result": json.dumps(summary, ensure_ascii=False, indent=2),
            "status": "completed_with_warnings" if state.get("errors") else "completed",
            "events": [_event("orchestrator", "completed", "Merged agent outputs")],
            "agent_events": {"orchestrator": _event("orchestrator", "completed", "Merged agent outputs")},
        }

    graph = StateGraph(CareerState)
    graph.add_node("orchestrator", orchestrator)
    graph.add_node("job_discovery", job_discovery)
    graph.add_node("resume_intelligence", resume_intelligence)
    graph.add_node("company_research", company_research)
    graph.add_node("skill_gap_analysis", skill_gap_analysis)
    graph.add_node("job_matching", job_matching)
    graph.add_node("preparation", preparation)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "orchestrator")
    # LangGraph executes these sibling nodes in parallel and joins before the
    # dependent analysis/matching stage.
    graph.add_edge("orchestrator", "job_discovery")
    graph.add_edge("orchestrator", "resume_intelligence")
    graph.add_edge("orchestrator", "company_research")
    graph.add_edge("resume_intelligence", "skill_gap_analysis")
    graph.add_edge(["job_discovery", "skill_gap_analysis", "company_research"], "job_matching")
    graph.add_edge("job_matching", "preparation")
    graph.add_edge("preparation", "finalize")
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
        "agent_events": {name: _event(name, "queued", "Waiting for dependencies") for name in AGENTS},
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
