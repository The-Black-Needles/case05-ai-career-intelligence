import json
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.blueprint = (ROOT / "docs/CASE05_PUBLIC_BLUEPRINT.md").read_text(
            encoding="utf-8"
        )
        cls.scoring = (ROOT / "docs/SCORING_MODEL_V2.md").read_text(
            encoding="utf-8"
        )
        cls.requirement_evidence_contract = (
            ROOT / "docs/REQUIREMENT_EVIDENCE_DEMO_CONTRACT.md"
        ).read_text(encoding="utf-8")
        cls.release_checklist = (
            ROOT / "docs/PUBLIC_RELEASE_CHECKLIST.md"
        ).read_text(encoding="utf-8")
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            cls.project = tomllib.load(project_file)["project"]
        cls.profile = json.loads(
            (ROOT / "config/profile.example.json").read_text(encoding="utf-8")
        )

    def document_section(self, document, heading, level=3):
        marker = f"{'#' * level} {heading}"
        lines = document.splitlines()
        try:
            start = lines.index(marker) + 1
        except ValueError:
            self.fail(f"Document section is missing: {marker}")

        end = next(
            (
                index
                for index in range(start, len(lines))
                if any(
                    lines[index].startswith(f"{'#' * heading_level} ")
                    for heading_level in range(1, level + 1)
                )
            ),
            len(lines),
        )
        return "\n".join(lines[start:end])

    def readme_section(self, heading):
        return self.document_section(self.readme, heading)

    def blueprint_section(self, heading):
        return self.document_section(self.blueprint, heading)

    def contract_section(self, heading):
        return self.document_section(
            self.requirement_evidence_contract, heading, level=2
        )

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
        self.assertIn("local,\nsynthetic requirement/evidence assessment demo", self.readme)
        self.assertIn("in-memory\n`PublicJobRecord` contract", self.readme)
        self.assertIn("do not establish an operational AI Job Radar", self.readme)
        implemented = self.readme_section("IMPLEMENTED").casefold()
        planned = self.readme_section("PLANNED / NOT ACTIVE").casefold()
        operational_capabilities = (
            "collection",
            "normalization",
            "loading",
            "transformation",
            "deduplication",
            "semantic classification",
            "semantic classification and requirement/evidence matching",
            "scoring",
            "ranking",
            "recommendation",
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

    def test_public_foundation_contracts_have_narrow_boundaries(self):
        implemented = self.blueprint_section("IMPLEMENTED").casefold()
        planned = self.blueprint_section("PLANNED / NOT ACTIVE").casefold()
        self.assertIn("in-memory `publicjobrecord` contract", implemented)
        self.assertIn("preserves supplied valid values", implemented)
        self.assertIn("local deterministic synthetic requirement/evidence assessment demo", implemented)
        for capability in (
            "collection",
            "loading",
            "transformation",
            "normalization",
            "deduplication",
            "classification",
            "semantic matching",
            "candidate readiness",
            "scoring",
            "ranking",
            "recommendation",
            "llm evaluation",
            "report",
            "agents",
            "security enforcement",
            "decision model runtime",
        ):
            with self.subTest(capability=capability):
                self.assertNotIn(capability, implemented)
                self.assertIn(capability, planned)

    def test_blueprint_truthfully_distinguishes_publication_guard(self):
        implemented = " ".join(
            self.blueprint_section("IMPLEMENTED").casefold().split()
        )
        planned = " ".join(
            self.blueprint_section("PLANNED / NOT ACTIVE").casefold().split()
        )

        self.assertIn("public-release sanitization check", implemented)
        self.assertNotIn("security enforcement", implemented)
        self.assertNotIn("production security system", implemented)
        self.assertNotIn(
            "operational career-intelligence capability",
            implemented,
        )
        self.assertNotIn("decision model runtime", implemented)

        self.assertIn("security enforcement", planned)
        self.assertIn(
            "the implemented public-release sanitization check is "
            "intentionally separate from this planned operational "
            "security enforcement.",
            planned,
        )
        self.assertIn(
            "it only inspects the current publication candidate; it is "
            "not a production security system, an operational "
            "career-intelligence capability, or a decision model runtime.",
            planned,
        )
        self.assertIn(
            "decision model v2 remains `draft_not_active`.",
            planned,
        )

    def test_scoring_model_is_draft_without_runtime_claims(self):
        self.assertIn("DRAFT_NOT_ACTIVE", self.scoring)
        self.assertIn("no executable weighted scoring", self.scoring)
        self.assertIn("Candidate Readiness assessment", self.scoring)
        self.assertIn("No code applies them", self.scoring)

    def test_requirement_evidence_contract_is_local_and_factual(self):
        status = self.contract_section("Status")
        purpose = self.contract_section("Purpose and boundary")
        linkage = self.document_section(
            self.requirement_evidence_contract,
            "Explicit linkage and validation",
        )
        assessment = self.contract_section("Implemented factual assessment")
        output = self.contract_section("Human review and output")
        command = self.contract_section("Implemented local command")
        status, purpose, linkage, assessment, output, command = (
            " ".join(section.split())
            for section in (status, purpose, linkage, assessment, output, command)
        )

        self.assertIn("IMPLEMENTATION_STATUS=IMPLEMENTED_LOCAL_DEMO", status)
        self.assertIn("P5B froze this design contract", status)
        self.assertIn("non-production", status)
        self.assertIn("data/demo_assessment.json", command)
        self.assertIn("not production-ready", command)

        self.assertIn("explicit linkage by IDs", purpose)
        self.assertIn("Explicit IDs are the only matching mechanism", linkage)
        self.assertIn("no semantic matching", linkage)

        self.assertIn("EXPLICIT_EVIDENCE_LINKED", assessment)
        self.assertIn("NO_EXPLICIT_EVIDENCE_LINK", assessment)
        self.assertIn("does not mean the requirement is satisfied", assessment)
        self.assertIn(
            "does not mean the candidate lacks a skill or capability", assessment
        )
        self.assertIn("must never be interpreted as an absence of capability", assessment)

        self.assertIn("aggregate raw counts by requirement type", assessment)
        self.assertIn("must not produce a readiness", assessment)
        self.assertIn("It has no scoring, readiness calculation", purpose)
        self.assertIn("`SCORING_MODEL_V2` is not activated", purpose)
        self.assertIn("`DRAFT_NOT_ACTIVE`", purpose)

        self.assertIn(
            "produces none of the following candidate/job recommendation", output
        )
        self.assertIn("`APPLY`", output)
        self.assertIn("`ELIGIBLE`", output)
        self.assertIn("`READY`", output)
        self.assertIn("not candidate assessments", output)

        self.assertIn("HUMAN_REVIEW_REQUIRED=YES", output)
        self.assertIn("reviewer remains responsible", output)
        self.assertIn("evidence is relevant, sufficient, and persuasive", output)

        self.assertIn("no semantic inference or automatic matching", purpose)
        self.assertIn("No LLM, embeddings, classifier, agent", purpose)
        self.assertIn("AI-assisted feature is part of this contract", purpose)
        self.assertIn("IMPLEMENTATION_STATUS=IMPLEMENTED_LOCAL_DEMO", self.blueprint)
        self.assertIn("Human review remains mandatory", self.blueprint)

    def test_readme_documents_only_the_local_synthetic_demo(self):
        command = (
            "PYTHONPATH=src python3 -m ai_job_radar.demo "
            "--assessment data/demo_assessment.json"
        )
        self.assertIn(command, self.readme)
        lowered = self.readme.casefold()
        for phrase in (
            "local,\nsynthetic",
            "no real-job collection",
            "semantic matching",
            "scoring",
            "recommendation",
            "llm/agent runtime",
            "production activity",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lowered)

    def test_public_release_checklist_gates_are_documented(self):
        release_doc = ROOT / "docs/PUBLIC_RELEASE_CHECKLIST.md"

        self.assertTrue(release_doc.is_file())
        self.assertIn("docs/PUBLIC_RELEASE_CHECKLIST.md", self.readme)
        self.assertIn("[MIT License](LICENSE)", self.readme)
        self.assertTrue((ROOT / "LICENSE").is_file())
        for command in (
            "PYTHONPATH=src python3 -m unittest discover -s tests",
            "PYTHONPATH=src python3 -m ai_job_radar.public_sanitizer",
        ):
            with self.subTest(command=command):
                self.assertIn(command, self.readme)
                self.assertIn(command, self.release_checklist)
        lowered = self.release_checklist.casefold()
        self.assertIn("public scaffold", lowered)
        self.assertIn("current candidate only", lowered)
        self.assertIn("mit license", lowered)

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
