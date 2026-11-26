import unittest

from app.services.scoring_v3 import score_resume_v3


def _policy(**overrides: object) -> dict[str, object]:
    policy: dict[str, object] = {
        "scoringPolicyVersion": 2,
        "skillsRequirement": "required",
        "experienceRequirement": "required",
        "experienceYears": 2,
        "educationRequirement": "required",
        "projectsRequirement": "required",
        "requiredSkills": ["Flutter", "REST APIs"],
        "requiredEducation": "BSCS or BSSE",
        "projectCriteria": ["mobile app", "Firebase integration"],
    }
    policy.update(overrides)
    return policy


def _role(source: str, title: str = "Flutter Developer") -> dict[str, object]:
    return {
        "title": title,
        "employer": "Example",
        "sourceText": source,
        "responsibilities": [source],
        "extractionConfidence": "high",
        "dateEvidence": {"range": "2020 - 2022"},
    }


def _score(
    *,
    skills: list[str] | None = None,
    employment: list[dict[str, object]] | None = None,
    education: list[str | dict[str, str]] | None = None,
    text: str = "",
    policy: dict[str, object] | None = None,
) -> dict[str, object]:
    effective_policy = policy or _policy()
    return score_resume_v3(
        skills or [],
        employment or [],
        education or [],
        text,
        "Flutter Developer",
        effective_policy.get("requiredSkills"),
        "",
        str(effective_policy.get("requiredEducation") or ""),
        "Build applications with Flutter and maintain code.",
        effective_policy,
    )


class ScoringV3Tests(unittest.TestCase):
    def test_fresh_graduate_and_experienced_candidate_get_neutral_entry_level_credit(
        self,
    ) -> None:
        policy = _policy(experienceRequirement="not_applicable")
        fresh_graduate = _score(policy=policy)
        experienced_candidate = _score(
            employment=[
                _role(
                    "Sales Executive 2015 - 2024. Lead generation and client acquisition.",
                    "Sales Executive",
                )
            ],
            policy=policy,
        )

        self.assertEqual(
            fresh_graduate["components"]["experience"]["score"],
            25.0,
        )
        self.assertEqual(
            experienced_candidate["components"]["experience"]["score"],
            25.0,
        )
        self.assertTrue(
            fresh_graduate["components"]["experience"]["neutralCredit"]
        )
        self.assertTrue(
            experienced_candidate["components"]["experience"]["neutralCredit"]
        )

    def test_not_applicable_experience_gets_neutral_full_credit(self) -> None:
        result = _score(
            policy=_policy(experienceRequirement="not_applicable"),
        )

        experience = result["components"]["experience"]
        self.assertEqual(experience["score"], 25.0)
        self.assertTrue(experience["neutralCredit"])

    def test_required_experience_uses_only_direct_dated_experience(self) -> None:
        cases = (
            ([], 0.0),
            ([_role("Flutter Developer 2020 - 2021. Build applications with Flutter.")], 12.5),
            ([_role("Flutter Developer 2020 - 2022. Build applications with Flutter.")], 25.0),
        )
        for employment, expected in cases:
            with self.subTest(expected=expected):
                result = _score(employment=employment)
                self.assertEqual(
                    result["components"]["experience"]["score"],
                    expected,
                )

    def test_experience_above_minimum_is_capped_at_full_credit(self) -> None:
        result = _score(
            employment=[
                _role("Flutter Developer 2020 - 2022. Build applications with Flutter.")
            ],
            policy=_policy(experienceYears=1),
        )

        self.assertEqual(result["components"]["experience"]["score"], 25.0)

    def test_unrelated_experience_is_not_credited(self) -> None:
        result = _score(
            employment=[
                _role(
                    "Sales Executive 2020 - 2024. Lead generation and client acquisition.",
                    "Sales Executive",
                )
            ]
        )

        self.assertEqual(result["components"]["experience"]["score"], 0.0)

    def test_overlapping_direct_roles_are_not_double_counted(self) -> None:
        result = _score(
            employment=[
                _role("Flutter Developer 2020 - 2022. Build applications with Flutter."),
                _role("Software Developer 2021 - 2023. Build applications with Flutter."),
            ]
        )

        self.assertEqual(
            result["components"]["experience"]["candidateDirectRelevantYears"],
            3.0,
        )
        self.assertEqual(result["components"]["experience"]["score"], 25.0)

    def test_skills_requirements_are_evidence_based_and_capped(self) -> None:
        result = _score(
            skills=["Flutter", "REST API", "REST API", "Flutter"],
        )

        skills = result["components"]["skills"]
        self.assertEqual(skills["score"], 40.0)
        self.assertEqual(skills["matchedCount"], 2)
        self.assertTrue(all(item["resumeSkillEvidence"] for item in skills["requirements"]))

    def test_common_technical_skill_aliases_are_case_insensitive(self) -> None:
        policy = _policy(
            requiredSkills=[
                "Flutter",
                "Dart",
                "Firebase",
                "REST API",
                "Git",
                "CI/CD",
            ]
        )
        result = _score(
            skills=[
                "FLUTTER FRAMEWORK",
                "Dart Language",
                "firebase",
                "REST APIs",
                "git",
                "ci/cd",
                "RESTful API",
            ],
            policy=policy,
        )

        skills = result["components"]["skills"]
        self.assertEqual(skills["score"], 40.0)
        self.assertEqual(skills["matchedCount"], 6)

    def test_duplicate_and_synonymous_requirements_are_counted_once(self) -> None:
        result = _score(
            skills=["flutter", "REST APIs"],
            policy=_policy(
                requiredSkills=[
                    "Flutter",
                    "FLUTTER",
                    "REST API",
                    "REST APIs",
                ]
            ),
        )

        skills = result["components"]["skills"]
        self.assertEqual(skills["requiredCount"], 2)
        self.assertEqual(skills["matchedCount"], 2)
        self.assertEqual(skills["score"], 40.0)
        self.assertEqual(len(skills["requirements"]), 2)

    def test_unrelated_skills_do_not_receive_credit(self) -> None:
        result = _score(
            skills=["Sales", "Customer service"],
            policy=_policy(requiredSkills=["Flutter"]),
        )

        self.assertEqual(result["components"]["skills"]["score"], 0.0)

    def test_missing_skills_and_education_score_zero(self) -> None:
        result = _score()

        self.assertEqual(result["components"]["skills"]["score"], 0.0)
        self.assertEqual(result["components"]["education"]["score"], 0.0)

    def test_not_applicable_skills_and_education_receive_zero(self) -> None:
        result = _score(
            policy=_policy(
                skillsRequirement="not_applicable",
                educationRequirement="not_applicable",
                experienceRequirement="not_applicable",
            )
        )

        self.assertEqual(result["components"]["skills"]["score"], 0.0)
        self.assertEqual(result["components"]["education"]["score"], 0.0)

    def test_education_uses_present_equivalent_qualification(self) -> None:
        result = _score(education=[{"text": "BSSE, completed"}])

        education = result["components"]["education"]
        self.assertEqual(education["score"], 20.0)
        self.assertEqual(education["qualification"], "BSSE")
        self.assertTrue(education["evidence"])

    def test_plural_masters_education_has_traceable_evidence(self) -> None:
        evidence = "Masters in Computer Science Aug 2006 - May 2008"
        result = _score(
            education=[{"text": evidence}],
            policy=_policy(
                requiredEducation=(
                    "BS Computer Science, Software Engineering, IT or equivalent"
                )
            ),
        )

        education = result["components"]["education"]
        self.assertEqual(education["score"], 20.0)
        self.assertEqual(education["qualification"], "Master")
        self.assertEqual(education["evidence"], [evidence])

    def test_practical_work_scores_distinct_explicit_contributions(self) -> None:
        result = _score(
            text=(
                "Built a mobile app with Flutter and Firebase integration, "
                "enabling offline access.\n"
                "Built a mobile app with Flutter and Firebase integration, "
                "enabling offline access.\n"
                "Implemented a responsive mobile app with Flutter."
            )
        )

        practical = result["components"]["practicalWork"]
        self.assertEqual(len(practical["evidence"]), 2)
        self.assertEqual(practical["score"], 8.0)
        self.assertTrue(all(item["reasonCodes"] for item in practical["evidence"]))

    def test_practical_work_without_explicit_relevant_contributions_is_zero(self) -> None:
        result = _score(text="Flutter, Firebase, REST API, and mobile application.")

        self.assertEqual(result["components"]["practicalWork"]["score"], 0.0)

    def test_project_only_candidate_can_earn_practical_work_marks(self) -> None:
        result = _score(
            text=(
                "Built a mobile app with Flutter and Firebase integration, "
                "enabling offline access."
            ),
            policy=_policy(experienceRequirement="not_applicable"),
        )

        self.assertEqual(result["components"]["experience"]["score"], 25.0)
        self.assertEqual(result["components"]["practicalWork"]["score"], 4.0)
        self.assertEqual(
            result["components"]["practicalWork"]["evidence"][0]["statement"],
            "Built a mobile app with Flutter and Firebase integration, enabling offline access.",
        )

    def test_achievement_without_projects_heading_is_evidence_based(self) -> None:
        statement = (
            "Improved Flutter application reliability through automated testing."
        )
        result = _score(text=statement)

        practical = result["components"]["practicalWork"]
        self.assertEqual(practical["score"], 5.0)
        self.assertEqual(
            [item["statement"] for item in practical["evidence"]],
            [statement],
        )
        self.assertIn("stated_outcome", practical["evidence"][0]["reasonCodes"])

    def test_practical_work_is_capped_and_duplicate_statements_are_not_recounted(
        self,
    ) -> None:
        contribution = (
            "Implemented Firebase integration in mobile app feature {index}, "
            "resulting in improved access."
        )
        statements = [
            contribution.format(index=index) for index in range(1, 6)
        ]
        result = _score(
            text="\n".join([*statements, statements[0], statements[1]]),
        )

        practical = result["components"]["practicalWork"]
        self.assertEqual(practical["score"], 15.0)
        self.assertEqual(practical["maxScore"], 15)
        self.assertEqual(len(practical["evidence"]), 5)
        self.assertEqual(
            len({item["statement"] for item in practical["evidence"]}),
            len(practical["evidence"]),
        )
        self.assertEqual(sum(item["points"] for item in practical["evidence"]), 25)

    def test_total_is_deterministic_and_bounded(self) -> None:
        arguments = {
            "skills": ["Flutter", "REST API"],
            "employment": [
                _role("Flutter Developer 2020 - 2022. Build applications with Flutter.")
            ],
            "education": [{"text": "BS Software Engineering, completed"}],
            "text": "Built a mobile app with Flutter and Firebase integration, enabling access.",
        }

        first = _score(**arguments)
        second = _score(**arguments)
        self.assertEqual(first, second)
        self.assertEqual(first["score"], 89.0)
        self.assertLessEqual(first["score"], first["maxScore"])


if __name__ == "__main__":
    unittest.main()
