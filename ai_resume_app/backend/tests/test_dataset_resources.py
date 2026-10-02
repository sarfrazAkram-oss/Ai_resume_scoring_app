import unittest

from app.services.dataset_resources import load_terms
from app.services.resume_structurer import extract_structured_information


class DatasetResourceTests(unittest.TestCase):
    def test_missing_resource_falls_back_to_empty_terms(self) -> None:
        self.assertEqual(load_terms("resource_that_does_not_exist"), ())

    def test_existing_resource_terms_can_support_structured_skills(self) -> None:
        result = extract_structured_information("SKILLS\nJavaScript\nFlutter\n")
        self.assertIn("JavaScript", result["skills"])
        self.assertIn("Flutter", result["skills"])

    def test_manual_skill_behavior_remains_boundary_safe(self) -> None:
        result = extract_structured_information("SKILLS\nC CSS Java JavaScript")
        self.assertIn("C", result["skills"])
        self.assertIn("CSS", result["skills"])
        self.assertIn("Java", result["skills"])
        self.assertIn("JavaScript", result["skills"])


if __name__ == "__main__":
    unittest.main()
