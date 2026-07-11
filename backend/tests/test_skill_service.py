import json
import os
import tempfile
import unittest

from services.skill_service import SkillService


class SkillServiceTests(unittest.TestCase):
    def test_loads_builtin_manifests_by_skill_id(self):
        service = SkillService()

        skills = service.list_skills()

        self.assertEqual(
            {skill["skill_id"] for skill in skills},
            {
                "paper_planner",
                "course_reviewer",
                "kb_maintainer",
                "modeling_problem_parser",
                "modeling_planner",
                "modeling_programmer",
            },
        )
        self.assertEqual(
            service.get_skill("paper_planner")["output_kind"],
            "paper_plan",
        )
        self.assertIsNone(service.get_skill("missing"))

    def test_rejects_manifest_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = os.path.join(tmp, "broken", "skill.json")
            os.makedirs(os.path.dirname(manifest_path))
            with open(manifest_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "skill_id": "broken",
                        "name": "Broken",
                        "description": "Missing output kind.",
                        "allowed_tools": [],
                        "prompt_template": "Do nothing.",
                    },
                    handle,
                )

            with self.assertRaisesRegex(ValueError, "output_kind"):
                SkillService(skills_dir=tmp).list_skills()

    def test_rejects_manifest_with_unregistered_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = os.path.join(tmp, "unsafe", "skill.json")
            os.makedirs(os.path.dirname(manifest_path))
            with open(manifest_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "skill_id": "unsafe",
                        "name": "Unsafe",
                        "description": "Attempts an unregistered action.",
                        "allowed_tools": ["shell"],
                        "prompt_template": "Run a shell command.",
                        "output_kind": "summary",
                    },
                    handle,
                )

            with self.assertRaisesRegex(ValueError, "shell"):
                SkillService(
                    skills_dir=tmp,
                    known_tools={"retrieve_sources", "create_output"},
                ).list_skills()


if __name__ == "__main__":
    unittest.main()
