import asyncio

from app.careerpilot import run_career_workflow


def test_career_graph_runs_parallel_stages_and_returns_agent_events():
    calls = []

    async def fake_model(messages, max_tokens=1200):
        calls.append(messages)
        system = messages[0]["content"].lower()
        if "convert the user's career/job-search goal" in system:
            return (
                '{"job_titles":["Data Scientist"],"locations":["Delhi NCR"],'
                '"salary_min_lpa":6,"salary_max_lpa":8,"experience":"entry level",'
                '"skills":["Python","SQL"],"constraints":[]}'
            )
        return '{"resume_guidance":"Use only supplied facts","drafts":[]}'

    async def fake_search(query):
        await asyncio.sleep(0)
        return [{
            "title": "Data Scientist — Example",
            "url": "https://jobs.example.com/data-scientist",
            "content": "Python SQL Delhi NCR",
        }]

    async def load_profile():
        return {
            "full_name": "Test Candidate",
            "skills": ["Python", "SQL"],
            "preferred_roles": ["Data Scientist"],
            "preferred_locations": ["Delhi NCR"],
        }

    result = asyncio.run(run_career_workflow(
        "Find Data Scientist roles in Delhi NCR with salary 6-8 LPA",
        model_call=fake_model,
        web_search_call=fake_search,
        profile_loader=load_profile,
        web_search=True,
    ))

    assert result["status"] == "completed"
    assert result["agent_count"] == 8
    assert result["agents"]["job_discovery"]["status"] == "completed"
    assert result["agents"]["resume_intelligence"]["status"] == "completed"
    assert result["agents"]["company_research"]["status"] == "skipped"
    assert result["agents"]["skill_gap_analysis"]["status"] == "completed"
    assert result["agents"]["job_matching"]["status"] == "completed"
    assert result["agents"]["resume_optimization"]["status"] == "completed"
    assert result["agents"]["outreach_drafting"]["status"] == "completed"
    assert result["agents"]["interview_preparation"]["status"] == "completed"
    assert len(calls) == 4
    assert "No application was submitted" in result["result"]


def test_career_graph_skips_web_search_when_disabled():
    async def fake_model(messages, max_tokens=1200):
        return '{"job_titles":["ML Engineer"],"locations":["Noida"],"skills":["Python"]}'

    async def forbidden_search(query):
        raise AssertionError("Web search must not run when disabled")

    result = asyncio.run(run_career_workflow(
        "Find ML Engineer jobs in Noida",
        model_call=fake_model,
        web_search_call=forbidden_search,
        profile_loader=lambda: asyncio.sleep(0, result={"skills": ["Python"]}),
        web_search=False,
    ))

    assert result["agents"]["job_discovery"]["status"] == "skipped"
