import unittest

from app.services.final_scorer import score_resume


def _complete_inputs() -> dict[str, object]:
    return {
        "resume_skills": ["Flutter", "Dart", "Firebase", "SQL"],
        "resume_experience": [
            {"text": "Flutter Developer at ABC Company - 2 years"}
        ],
        "resume_education": [
            {"text": "Software Engineering (BSSE), completed"}
        ],
        "resume_projects": [
            {"text": "Quran Learning App developed using Flutter, Dart and Firebase"}
        ],
        "job_title": "Flutter Developer",
        "required_skills": "Flutter, Dart, Firebase, REST API",
        "required_experience": "Minimum 2 years",
        "required_education": "BSCS or BSSE",
        "job_description": "Build and maintain Flutter applications.",
    }


def _score(**overrides: object) -> dict[str, object]:
    inputs = _complete_inputs()
    inputs.update(overrides)
    return score_resume(**inputs)  # type: ignore[arg-type]


class FinalScorerTests(unittest.TestCase):
    def test_all_four_components_scored(self) -> None:
        result = _score()
        self.assertEqual(result["skills"]["skillsScore"], 30.0)
        self.assertEqual(result["experience"]["experienceScore"], 25.0)
        self.assertEqual(result["education"]["educationScore"], 20.0)
        self.assertEqual(result["projects"]["projectsScore"], 11.25)
        self.assertEqual(result["earnedScore"], 86.25)
        self.assertEqual(result["availableMaxScore"], 100)
        self.assertEqual(result["finalScore"], 86.25)

    def test_missing_experience_is_excluded_and_normalized(self) -> None:
        result = _score(required_experience="")
        self.assertIsNone(result["experience"]["experienceScore"])
        self.assertEqual(result["earnedScore"], 61.25)
        self.assertEqual(result["availableMaxScore"], 75)
        self.assertEqual(result["finalScore"], 81.67)

    def test_missing_education_is_excluded_and_normalized(self) -> None:
        result = _score(required_education="")
        self.assertIsNone(result["education"]["educationScore"])
        self.assertEqual(result["availableMaxScore"], 80)
        self.assertEqual(result["finalScore"], 82.81)

    def test_missing_required_skills_also_excludes_projects(self) -> None:
        result = _score(required_skills=None)
        self.assertIsNone(result["skills"]["skillsScore"])
        self.assertIsNone(result["projects"]["projectsScore"])
        self.assertEqual(result["availableMaxScore"], 45)
        self.assertEqual(result["finalScore"], 100.0)

    def test_multiple_missing_requirements_normalize_remaining_components(self) -> None:
        result = _score(required_skills="", required_experience="")
        self.assertIsNone(result["skills"]["skillsScore"])
        self.assertIsNone(result["projects"]["projectsScore"])
        self.assertIsNone(result["experience"]["experienceScore"])
        self.assertEqual(result["availableMaxScore"], 20)
        self.assertEqual(result["finalScore"], 100.0)

    def test_all_requirements_missing_returns_null_final_score(self) -> None:
        result = _score(
            required_skills=None,
            required_experience="",
            required_education="",
        )
        self.assertEqual(result["earnedScore"], 0.0)
        self.assertEqual(result["availableMaxScore"], 0)
        self.assertIsNone(result["finalScore"])
        self.assertEqual(result["status"], "not_scored_no_requirements")

    def test_zero_candidate_match_with_valid_requirements_scores_zero(self) -> None:
        result = _score(
            resume_skills=[],
            resume_experience=[],
            resume_education=[{"text": "MBBS"}],
            resume_projects=[],
            required_education="Bachelor's degree in Computer Science",
        )
        self.assertEqual(result["earnedScore"], 0.0)
        self.assertEqual(result["availableMaxScore"], 100)
        self.assertEqual(result["finalScore"], 0.0)

    def test_perfect_score_is_100(self) -> None:
        result = _score(
            resume_skills=["Flutter", "Dart", "Firebase", "REST API"],
            resume_experience=[{"text": "4 years"}],
            resume_education=[{"text": "Completed BSSE"}],
            resume_projects=[{"text": "Flutter Dart Firebase REST API"}],
        )
        self.assertEqual(result["earnedScore"], 100.0)
        self.assertEqual(result["finalScore"], 100.0)

    def test_final_score_never_exceeds_100(self) -> None:
        result = _score(
            resume_skills=["Flutter", "Dart", "Firebase", "REST API"],
            resume_experience=[{"text": "20 years"}],
            resume_education=[{"text": "Completed BSSE"}],
            resume_projects=[{"text": "Flutter Dart Firebase REST API"}],
        )
        self.assertLessEqual(result["finalScore"], 100.0)

    def test_final_score_and_earned_score_round_to_two_decimals(self) -> None:
        result = _score(
            resume_skills=["Flutter"],
            resume_experience=[],
            resume_education=[],
            resume_projects=[{"text": "Flutter"}],
            required_skills="Flutter, Dart, Firebase",
            required_experience="",
            required_education="",
        )
        self.assertEqual(result["earnedScore"], 18.33)
        self.assertEqual(result["availableMaxScore"], 55)
        self.assertEqual(result["finalScore"], 33.33)

    def test_in_progress_education_component_is_preserved(self) -> None:
        result = _score(
            resume_skills=[],
            resume_experience=[],
            resume_education=[{"text": "BSSE, 7th semester"}],
            resume_projects=[],
            required_skills="",
            required_experience="",
        )
        self.assertEqual(result["education"]["educationScore"], 15.0)
        self.assertEqual(result["education"]["status"], "scored_in_progress")
        self.assertEqual(result["availableMaxScore"], 20)
        self.assertEqual(result["finalScore"], 75.0)

    def test_component_status_values_are_preserved(self) -> None:
        result = _score(required_experience="")
        self.assertEqual(result["skills"]["status"], "scored")
        self.assertEqual(
            result["experience"]["status"],
            "not_scored_no_parseable_requirement",
        )
        self.assertEqual(result["education"]["status"], "scored")
        self.assertEqual(result["projects"]["status"], "scored")


if __name__ == "__main__":
    unittest.main()