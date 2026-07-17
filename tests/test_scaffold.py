import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTest(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "README.md",
            "pyproject.toml",
            "docs/CASE06_PUBLIC_BLUEPRINT.md",
            "docs/SCORING_MODEL_V2.md",
            "config/profile.example.json",
            "config/companies.example.json",
            "data/reference_jobs.json",
        ]

        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_weights_sum_to_one(self):
        profile = json.loads(
            (ROOT / "config/profile.example.json").read_text(encoding="utf-8")
        )
        self.assertAlmostEqual(sum(profile["weights"].values()), 1.0)

    def test_weekly_limits(self):
        profile = json.loads(
            (ROOT / "config/profile.example.json").read_text(encoding="utf-8")
        )
        weekly = profile["weekly_report"]
        self.assertEqual(weekly["max_detailed_jobs"], 15)
        self.assertEqual(weekly["max_jobs_per_company"], 3)
        self.assertTrue(weekly["repeat_only_on_material_change"])


if __name__ == "__main__":
    unittest.main()
