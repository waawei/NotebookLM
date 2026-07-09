import asyncio
import unittest

from api import agents, skills


class FakeSkillService:
    def list_skills(self):
        return [{"skill_id": "paper_planner", "name": "Paper Planner"}]

    def get_skill(self, skill_id):
        if skill_id == "paper_planner":
            return {"skill_id": "paper_planner", "name": "Paper Planner"}
        return None


class FakeAgentService:
    def __init__(self):
        self.runs = {}

    def create_run(self, skill_id, input_payload):
        run = {"run_id": "run-1", "skill_id": skill_id, "status": "running", "input_payload": input_payload, "steps": []}
        self.runs[run["run_id"]] = run
        return run

    async def execute_run(self, run_id):
        return self.runs[run_id]

    def get_run(self, run_id):
        return self.runs.get(run_id)

    def list_runs(self):
        return list(self.runs.values())


class AgentsApiTests(unittest.TestCase):
    def setUp(self):
        self.original_skills = skills.skill_service
        self.original_agents = agents.agent_service
        skills.skill_service = FakeSkillService()
        agents.agent_service = FakeAgentService()

    def tearDown(self):
        skills.skill_service = self.original_skills
        agents.agent_service = self.original_agents

    def test_lists_skills_without_exposing_internal_configuration(self):
        response = asyncio.run(skills.list_skills())

        self.assertEqual(response["skills"][0]["skill_id"], "paper_planner")

    def test_creates_and_loads_inspectable_agent_run(self):
        created = asyncio.run(
            agents.create_run(
                agents.AgentRunCreate(skill_id="paper_planner", doc_ids=["doc-1"], request="Plan"),
                background_tasks=None,
            )
        )
        listed = asyncio.run(agents.list_runs())
        loaded = asyncio.run(agents.get_run(created["run_id"]))

        self.assertEqual(created["status"], "running")
        self.assertEqual(listed["total"], 1)
        self.assertEqual(loaded["input_payload"]["doc_ids"], ["doc-1"])


if __name__ == "__main__":
    unittest.main()
