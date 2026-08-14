import json
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.scoring = (ROOT / "docs/SCORING_MODEL_V2.md").read_text(
            encoding="utf-8"
        )
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            cls.project = tomllib.load(project_file)["project"]
        cls.profile = json.loads(
            (ROOT / "config/profile.example.json").read_text(encoding="utf-8")
        )

    def readme_section(self, heading):
        marker = f"### {heading}"
        lines = self.readme.splitlines()
        try:
            start = lines.index(marker) + 1
        except ValueError:
            self.fail(f"README section is missing: {marker}")

        end = next(
            (
                index
                for index in range(start, len(lines))
                if lines[index].startswith("### ")
                or lines[index].startswith("## ")
                or lines[index].startswith("# ")
            ),
            len(lines),
        )
        return "\n".join(lines[start:end])

    def test_case_05_identity_and_blueprint_rename(self):
        identity = (
            "Case 05 — AI Career Intelligence — "
            "Intelligent Job Opportunity Decision System"
        )
        blueprint = ROOT / "docs/CASE05_PUBLIC_BLUEPRINT.md"

        self.assertIn("# Case 05 — AI Career Intelligence", self.readme)
        self.assertIn("Intelligent Job Opportunity Decision System", self.readme)
        self.assertTrue(blueprint.is_file())
        self.assertIn(identity, blueprint.read_text(encoding="utf-8"))
        self.assertFalse((ROOT / "docs/CASE06_PUBLIC_BLUEPRINT.md").exists())

    def test_project_metadata_has_no_dependencies(self):
        self.assertEqual(self.project["name"], "case05-ai-career-intelligence")
        self.assertEqual(self.project["version"], "0.1.0")
        self.assertEqual(self.project["dependencies"], [])

    def test_status_is_explicit_and_truthful(self):
        self.assertIn("only a scaffold", self.readme)
        implemented = self.readme_section("IMPLEMENTED").casefold()
        planned = self.readme_section("PLANNED / NOT ACTIVE").casefold()
        operational_capabilities = (
            "collection",
            "normalization",
            "deduplication",
            "semantic classification",
            "scoring",
            "candidate readiness",
            "llm evaluation",
            "reporting",
            "security enforcement",
            "agents",
            "decision model runtime",
        )

        for capability in operational_capabilities:
            with self.subTest(capability=capability):
                self.assertNotIn(capability, implemented)
                self.assertIn(capability, planned)

    def test_scoring_model_is_draft_without_runtime_claims(self):
        self.assertIn("DRAFT_NOT_ACTIVE", self.scoring)
        self.assertIn("no executable weighted scoring", self.scoring)
        self.assertIn("Candidate Readiness assessment", self.scoring)
        self.assertIn("No code applies them", self.scoring)

    def test_reference_dataset_is_empty(self):
        reference = json.loads(
            (ROOT / "data/reference_jobs.json").read_text(encoding="utf-8")
        )
        self.assertEqual(reference["jobs"], [])
        description = reference["description"].casefold()
        self.assertIn("empty", description)
        self.assertIn("placeholder", description)
        self.assertTrue(
            "future" in description or "reserved" in description,
            "reference dataset description must make its future/reserved nature clear",
        )

    def test_example_configuration_is_synthetic(self):
        companies = json.loads(
            (ROOT / "config/companies.example.json").read_text(encoding="utf-8")
        )
        self.assertIn("synthetic", self.profile["profile_id"])
        self.assertEqual(companies["companies"][0]["source_type"], "synthetic")
        self.assertFalse(companies["companies"][0]["active"])

    def test_existing_draft_configuration_invariants(self):
        self.assertAlmostEqual(sum(self.profile["weights"].values()), 1.0)
        weekly = self.profile["weekly_report"]
        self.assertEqual(weekly["max_detailed_jobs"], 15)
        self.assertEqual(weekly["max_jobs_per_company"], 3)
        self.assertTrue(weekly["repeat_only_on_material_change"])


if __name__ == "__main__":
    unittest.main()
