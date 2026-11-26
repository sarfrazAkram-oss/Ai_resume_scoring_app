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
    def _policy(self, **overrides: str) -> dict[str, object]:
        policy: dict[str, object] = {
            "scoringPolicyVersion": 2,
            "skillsRequirement": "required",
            "experienceRequirement": "required",
            "experienceYears": 2,
            "educationRequirement": "required",
            "projectsRequirement": "required",
            "requiredSkills": "Python",
            "requiredEducation": "BSCS",
            "projectCriteria": "Mobile application",
        }
        policy.update(overrides)
        return policy

    def _score_policy(
        self,
        *,
        experience: list[dict[str, str]] | None = None,
        skills: list[str] | None = None,
        education: list[dict[str, str]] | None = None,
        projects: list[dict[str, str]] | None = None,
        policy: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return score_resume(
            skills or [],
            experience or [],
            education or [],
            projects or [],
            "Developer",
            "Python",
            "",
            "BSCS",
            "",
            job_policy=policy or self._policy(),
        )

    def test_internship_without_experience_requirement(self) -> None:
        result = self._score_policy(
            skills=["Python"],
            education=[{"text": "BSCS"}],
            policy=self._policy(
                experienceRequirement="not_applicable",
                projectsRequirement="not_applicable",
            ),
        )

        self.assertIsNone(result["experience"]["experienceScore"])
        self.assertEqual(result["experience"]["maxScore"], 0)
        self.assertEqual(result["availableMaxScore"], 60)
        self.assertEqual(result["finalScore"], 100.0)

    def test_required_two_year_experience_scores_proportionally(self) -> None:
        policy = self._policy(
            skillsRequirement="not_applicable",
            educationRequirement="not_applicable",
            projectsRequirement="not_applicable",
        )
        cases = (([], 0.0), ([{"text": "1 year"}], 12.5),
                 ([{"text": "2 years"}], 25.0), ([{"text": "3 years"}], 25.0))

        for experience, expected in cases:
            with self.subTest(experience=experience):
                result = self._score_policy(experience=experience, policy=policy)
                self.assertEqual(result["experience"]["experienceScore"], expected)
                self.assertEqual(result["availableMaxScore"], 25)
                self.assertGreaterEqual(result["finalScore"], 0)
                self.assertLessEqual(result["finalScore"], 100)

    def test_preferred_experience_is_scored_without_rejection(self) -> None:
        result = self._score_policy(
            experience=[],
            policy=self._policy(
                experienceRequirement="preferred",
                skillsRequirement="not_applicable",
                educationRequirement="not_applicable",
                projectsRequirement="not_applicable",
            ),
        )

        self.assertEqual(result["experience"]["experienceScore"], 0.0)
        self.assertEqual(result["experience"]["status"], "scored_preferred")
        self.assertEqual(result["finalScore"], 0.0)

    def test_projects_not_applicable_excludes_its_weight(self) -> None:
        result = self._score_policy(
            skills=["Python"],
            experience=[{"text": "2 years"}],
            education=[{"text": "BSCS"}],
            policy=self._policy(projectsRequirement="not_applicable"),
        )

        self.assertEqual(result["projects"]["maxScore"], 0)
        self.assertEqual(result["availableMaxScore"], 85)

    def test_required_projects_without_evidence_score_zero(self) -> None:
        result = self._score_policy(
            skills=["Python"],
            experience=[{"text": "2 years"}],
            education=[{"text": "BSCS"}],
            projects=[],
        )

        self.assertEqual(result["projects"]["projectsScore"], 0.0)
        self.assertEqual(result["projects"]["maxScore"], 15)

    def test_project_criteria_do_not_fall_back_to_required_skills(self) -> None:
        result = self._score_policy(
            projects=[{"text": "Python application"}],
            policy=self._policy(projectCriteria="Mobile application"),
        )

        self.assertEqual(result["projects"]["projectsScore"], 0.0)
        self.assertEqual(result["projects"]["missingProjectSkills"], ["Mobile application"])

    def test_missing_required_skills_and_education_score_zero(self) -> None:
        result = self._score_policy(
            skills=[],
            education=[],
            experience=[],
            projects=[],
        )

        self.assertEqual(result["skills"]["skillsScore"], 0.0)
        self.assertEqual(result["education"]["educationScore"], 0.0)
        self.assertEqual(result["availableMaxScore"], 100)

    def test_job_policy_denominator_is_identical_for_candidates(self) -> None:
        policy = self._policy(projectsRequirement="not_applicable")
        complete = self._score_policy(
            skills=["Python"],
            experience=[{"text": "2 years"}],
            education=[{"text": "BSCS"}],
            policy=policy,
        )
        missing_sections = self._score_policy(policy=policy)

        self.assertEqual(complete["availableMaxScore"], 85)
        self.assertEqual(
            missing_sections["availableMaxScore"],
            complete["availableMaxScore"],
        )

    def test_all_not_applicable_categories_produce_no_score(self) -> None:
        result = self._score_policy(
            policy=self._policy(
                skillsRequirement="not_applicable",
                experienceRequirement="not_applicable",
                educationRequirement="not_applicable",
                projectsRequirement="not_applicable",
            ),
        )

        self.assertIsNone(result["finalScore"])
        self.assertEqual(result["availableMaxScore"], 0)

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

    def test_flutter_candidate_outscores_unrelated_marketing_candidate(self) -> None:
        policy = self._policy(
            requiredSkills=["Flutter", "Dart", "Firebase"],
            requiredEducation="BSCS or BSSE",
            experienceYears=2,
            projectCriteria="Flutter mobile application",
        )
        relevant = score_resume(
            ["Flutter", "Dart", "Firebase"],
            [{"text": "2 years"}],
            [{"text": "Completed BSSE"}],
            [{"text": "Flutter mobile application"}],
            "Flutter Developer",
            policy["requiredSkills"],
            "",
            str(policy["requiredEducation"]),
            "",
            job_policy=policy,
        )
        unrelated = score_resume(
            ["SEO", "Content Marketing", "Google Ads"],
            [{"text": "2 years"}],
            [{"text": "Marketing degree"}],
            [{"text": "Marketing campaign"}],
            "Flutter Developer",
            policy["requiredSkills"],
            "",
            str(policy["requiredEducation"]),
            "",
            job_policy=policy,
        )

        self.assertEqual(relevant["finalScore"], 100.0)
        self.assertEqual(unrelated["experience"]["experienceScore"], 25.0)
        self.assertEqual(unrelated["finalScore"], 25.0)
        self.assertLess(unrelated["finalScore"], relevant["finalScore"])

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