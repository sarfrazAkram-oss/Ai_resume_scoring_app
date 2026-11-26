import unittest
from pathlib import Path


class CandidateProjectionRulesTests(unittest.TestCase):
    def test_projection_rules_require_safe_initial_shape_and_hr_updates(self) -> None:
        rules = (
            Path(__file__).resolve().parents[2] / "firestore.rules"
        ).read_text(encoding="utf-8")

        self.assertIn("getAfter(", rules)
        self.assertIn("keys().hasAll", rules)
        self.assertIn("keys().hasOnly", rules)
        self.assertIn("request.resource.data.status == 'Pending'", rules)
        self.assertIn("request.resource.data.scoreShared == false", rules)
        self.assertIn("resource.data.recruiterId == request.auth.uid", rules)
        self.assertNotIn("resource.data.candidateId == request.auth.uid;\n      allow update", rules)


if __name__ == "__main__":
    unittest.main()
