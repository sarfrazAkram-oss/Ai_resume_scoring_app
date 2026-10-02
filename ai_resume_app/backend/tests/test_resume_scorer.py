import unittest

from app.services.resume_scorer import score_experience, score_skills


class ScoreSkillsTests(unittest.TestCase):
    def test_example_partial_match(self) -> None:
        result = score_skills(
            ["Flutter", "Dart", "Firebase", "SQL"],
            "Flutter, Dart, Firebase, REST API",
        )
        self.assertEqual(result["matchedSkills"], ["Flutter", "Dart", "Firebase"])
        self.assertEqual(result["missingSkills"], ["REST API"])
        self.assertEqual(result["requiredSkillsCount"], 4)
        self.assertEqual(result["matchedSkillsCount"], 3)
        self.assertEqual(result["matchPercentage"], 75.0)
        self.assertEqual(result["skillsScore"], 30.0)
        self.assertEqual(result["status"], "scored")

    def test_exact_and_case_insensitive_matches(self) -> None:
        result = score_skills(["fLuTtEr", "DART"], ["Flutter", "Dart"])
        self.assertEqual(result["matchedSkills"], ["Flutter", "Dart"])
        self.assertEqual(result["skillsScore"], 40.0)


class ScoreExperienceTests(unittest.TestCase):
    def test_exact_experience_match(self) -> None:
        result = score_experience([{"text": "2 years"}], "2 years")
        self.assertEqual(result["candidateYears"], 2.0)
        self.assertEqual(result["requiredYears"], 2.0)
        self.assertEqual(result["matchPercentage"], 100.0)
        self.assertEqual(result["experienceScore"], 25.0)

    def test_candidate_below_requirement(self) -> None:
        result = score_experience([{"text": "1 year"}], "Minimum 2 years")
        self.assertEqual(result["matchPercentage"], 50.0)
        self.assertEqual(result["experienceScore"], 12.5)

    def test_candidate_above_requirement_is_capped(self) -> None:
        result = score_experience([{"text": "4 years"}], "2 years")
        self.assertEqual(result["matchPercentage"], 100.0)
        self.assertEqual(result["experienceScore"], 25.0)

    def test_six_months(self) -> None:
        result = score_experience([{"text": "6 months"}], "1 year")
        self.assertEqual(result["candidateYears"], 0.5)
        self.assertEqual(result["experienceScore"], 12.5)

    def test_requirement_ranges_use_minimum(self) -> None:
        for requirement in ("1-2 years", "1 to 2 years"):
            with self.subTest(requirement=requirement):
                result = score_experience([{"text": "1 year"}], requirement)
                self.assertEqual(result["requiredYears"], 1.0)
                self.assertEqual(result["experienceScore"], 25.0)

    def test_supported_requirement_phrasing(self) -> None:
        cases = (
            ("2 years", 2.0),
            ("2+ years", 2.0),
            ("Minimum 3 years", 3.0),
            ("3 years of experience", 3.0),
            ("1-2 years", 1.0),
            ("1 to 2 years", 1.0),
            ("6 months", 0.5),
            ("Fresh graduate", 0.0),
            ("Entry level", 0.0),
        )
        for requirement, expected_years in cases:
            with self.subTest(requirement=requirement):
                result = score_experience([], requirement)
                self.assertEqual(result["requiredYears"], expected_years)

    def test_month_and_year_date_ranges(self) -> None:
        month_range = score_experience(
            [{"text": "Jan 2023 - Jan 2025"}], "2 years"
        )
        year_range = score_experience([{"text": "2022 - 2024"}], "2 years")
        self.assertEqual(month_range["candidateYears"], 2.0)
        self.assertEqual(year_range["candidateYears"], 2.0)
        self.assertEqual(month_range["experienceScore"], 25.0)
        self.assertEqual(year_range["experienceScore"], 25.0)

    def test_multiple_distinct_entries_are_summed(self) -> None:
        result = score_experience(
            [{"text": "1 year at Company A"}, {"text": "6 months at Company B"}],
            "2 years",
        )
        self.assertEqual(result["candidateYears"], 1.5)
        self.assertEqual(result["experienceScore"], 18.75)

    def test_duplicate_duration_evidence_in_one_entry_not_summed(self) -> None:
        result = score_experience(
            [{"text": "2 years (24 months) of experience"}], "3 years"
        )
        self.assertEqual(result["candidateYears"], 2.0)

    def test_overlapping_date_ranges_in_one_entry_are_merged(self) -> None:
        result = score_experience(
            [{"text": "Jan 2020 - Jan 2022; Jan 2021 - Jan 2023"}], "3 years"
        )
        self.assertEqual(result["candidateYears"], 3.0)

    def test_fresh_graduate_and_entry_level_require_no_experience(self) -> None:
        for requirement in ("Fresh graduate", "Entry level"):
            with self.subTest(requirement=requirement):
                result = score_experience([], requirement)
                self.assertEqual(result["requiredYears"], 0.0)
                self.assertEqual(result["experienceScore"], 25.0)
                self.assertEqual(result["status"], "scored_no_experience_required")

    def test_empty_and_unparseable_requirements_are_not_scored(self) -> None:
        for requirement in ("", "Relevant background preferred"):
            with self.subTest(requirement=requirement):
                result = score_experience([{"text": "2 years"}], requirement)
                self.assertIsNone(result["matchPercentage"])
                self.assertIsNone(result["experienceScore"])
                self.assertEqual(
                    result["status"], "not_scored_no_parseable_requirement"
                )

    def test_requirement_without_candidate_duration_scores_zero(self) -> None:
        result = score_experience([{"text": "Software Engineer at Example Co."}], "2 years")
        self.assertEqual(result["candidateYears"], 0.0)
        self.assertEqual(result["matchPercentage"], 0.0)
        self.assertEqual(result["experienceScore"], 0.0)
        self.assertEqual(result["status"], "scored")


class ScoreSkillsRemainingTests(unittest.TestCase):
    def test_explicit_aliases(self) -> None:
        result = score_skills(
            ["JS", "nextjs", "nodejs", "ReactJS", "Flutter Framework"],
            ["JavaScript", "Next.js", "Node.js", "React", "Flutter"],
        )
        self.assertEqual(
            result["matchedSkills"],
            ["JavaScript", "Next.js", "Node.js", "React", "Flutter"],
        )
        self.assertEqual(result["skillsScore"], 40.0)

    def test_duplicate_resume_and_requirements_are_removed(self) -> None:
        result = score_skills(
            ["Python", " python ", "PYTHON", "SQL"],
            ["Python", " python ", "SQL", "sql"],
        )
        self.assertEqual(result["requiredSkillsCount"], 2)
        self.assertEqual(result["matchedSkills"], ["Python", "SQL"])
        self.assertEqual(result["skillsScore"], 40.0)

    def test_string_requirements_split_by_comma_newline_and_semicolon(self) -> None:
        result = score_skills(
            ["Python", "Dart", "SQL"],
            "Python, Dart\nSQL; Flutter",
        )
        self.assertEqual(result["requiredSkillsCount"], 4)
        self.assertEqual(result["matchedSkills"], ["Python", "Dart", "SQL"])
        self.assertEqual(result["missingSkills"], ["Flutter"])

    def test_zero_matches(self) -> None:
        result = score_skills(["Python"], ["Dart", "Flutter"])
        self.assertEqual(result["matchedSkills"], [])
        self.assertEqual(result["missingSkills"], ["Dart", "Flutter"])
        self.assertEqual(result["matchPercentage"], 0.0)
        self.assertEqual(result["skillsScore"], 0.0)

    def test_all_matches(self) -> None:
        result = score_skills(["Python", "Dart"], ["Dart", "Python"])
        self.assertEqual(result["matchPercentage"], 100.0)
        self.assertEqual(result["skillsScore"], 40.0)

    def test_missing_requirements_not_scored(self) -> None:
        for requirements in ("", " , ; \n", []):
            result = score_skills(["Python"], requirements)
            self.assertIsNone(result["matchPercentage"])
            self.assertIsNone(result["skillsScore"])
            self.assertEqual(result["matchedSkills"], [])
            self.assertEqual(result["missingSkills"], [])
            self.assertEqual(result["status"], "not_scored_no_requirements")

    def test_c_does_not_match_css(self) -> None:
        result = score_skills(["CSS"], ["C"])
        self.assertEqual(result["matchedSkills"], [])
        self.assertEqual(result["missingSkills"], ["C"])

    def test_java_does_not_match_javascript(self) -> None:
        result = score_skills(["JavaScript"], ["Java"])
        self.assertEqual(result["matchedSkills"], [])
        self.assertEqual(result["missingSkills"], ["Java"])

    def test_harmless_surrounding_punctuation(self) -> None:
        result = score_skills(["( Flutter! ", "[Dart]."], ["Flutter", "Dart"])
        self.assertEqual(result["matchedSkills"], ["Flutter", "Dart"])


if __name__ == "__main__":
    unittest.main()