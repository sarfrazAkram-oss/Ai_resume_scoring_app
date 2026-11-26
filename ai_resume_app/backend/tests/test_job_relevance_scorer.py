import unittest

from app.services.job_relevance_scorer import (
    RELEVANCE_MATCHER_VERSION,
    score_job_relevance,
)


def role(title, source, *, current=False, internship=False, confidence="high"):
    return {
        "title": title,
        "employer": "Example Employer",
        "startDateEvidence": None,
        "endDateEvidence": None,
        "isCurrent": current,
        "responsibilities": [source],
        "technologiesAndTools": [],
        "sourceText": source,
        "isInternship": internship,
        "extractionConfidence": confidence,
        "evidenceStatus": "structured" if confidence == "high" else "ambiguous",
    }


def analyze(title, description, evidence, skills=(), experience="2 years"):
    return score_job_relevance(title, description, skills, experience, evidence)


class JobRelevanceScorerTests(unittest.TestCase):
    def test_flutter_developer_matches_flutter_job_with_role_duties(self):
        result = analyze(
            "Flutter Developer",
            "Build applications with Flutter and maintain code.",
            [role(
                "Flutter Developer",
                "Flutter Developer at Acme 2020 - 2022. "
                "Build applications with Flutter and maintain code.",
            )],
            ["Flutter"],
        )
        self.assertEqual(result["relevanceMatcherVersion"], RELEVANCE_MATCHER_VERSION)
        self.assertEqual(result["roles"][0]["relevanceStatus"], "direct")
        self.assertIn("Flutter", result["roles"][0]["matchedJobRequirements"])
        self.assertEqual(result["totalDirectRelevantMonths"], 24)

    def test_sales_role_does_not_match_flutter_or_global_skill(self):
        result = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [role(
                "Sales Executive",
                "Sales Executive at Acme 2020 - 2022. "
                "Lead generation and client acquisition.",
            )],
            ["Flutter"],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "unrelated")
        self.assertEqual(result["roles"][0]["matchedJobRequirements"], [])
        self.assertEqual(result["totalDirectRelevantMonths"], 0)

    def test_nursing_duties_match_but_generic_hospital_work_is_ambiguous(self):
        nursing = analyze(
            "Registered Nurse",
            "Patient care and administer medication.",
            [role(
                "Nurse",
                "Nurse at City Hospital 2020 - 2022. "
                "Patient care and administer medication.",
            )],
        )
        generic = analyze(
            "Registered Nurse",
            "Patient care and administer medication.",
            [role(
                "Hospital Assistant",
                "Hospital Assistant at City Hospital 2020 - 2022.",
            )],
        )
        self.assertEqual(nursing["roles"][0]["relevanceStatus"], "direct")
        self.assertEqual(generic["roles"][0]["relevanceStatus"], "insufficient_evidence")

    def test_engineering_cad_design_evidence_matches(self):
        result = analyze(
            "Mechanical Engineer",
            "CAD design and technical drawings.",
            [role(
                "CAD Designer",
                "CAD Designer at Acme 2020 - 2022. CAD design and technical drawings.",
            )],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "direct")

    def test_seo_campaign_duties_match_marketing_job(self):
        result = analyze(
            "SEO Specialist",
            "Run SEO campaigns and improve organic search.",
            [role(
                "Marketing Specialist",
                "Marketing Specialist at Acme 2020 - 2022. "
                "SEO campaigns and search engine optimization improved organic search.",
            )],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "direct")

    def test_bookkeeping_and_reporting_match_accounting_job(self):
        result = analyze(
            "Accountant",
            "Bookkeeping and financial reporting.",
            [role(
                "Finance Clerk",
                "Finance Clerk at Acme 2020 - 2022. "
                "Bookkeeping and financial reporting.",
            )],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "direct")

    def test_recruitment_and_onboarding_match_hr_job(self):
        result = analyze(
            "HR Specialist",
            "Recruitment and employee onboarding.",
            [role(
                "Recruiter",
                "Recruiter at Acme 2020 - 2022. "
                "Recruitment and employee onboarding.",
            )],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "direct")

    def test_lead_generation_and_client_acquisition_match_sales_job(self):
        result = analyze(
            "Sales Executive",
            "Lead generation and client acquisition.",
            [role(
                "Account Manager",
                "Account Manager at Acme 2020 - 2022. "
                "Lead generation and client acquisition.",
            )],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "direct")

    def test_related_duties_can_match_different_job_titles(self):
        result = analyze(
            "Sales Executive",
            "Lead generation and client acquisition.",
            [role(
                "Account Manager",
                "Account Manager at Acme 2020 - 2022. "
                "Lead generation and client acquisition.",
            )],
        )
        self.assertLess(result["roles"][0]["roleTitleSimilarity"], 1.0)
        self.assertEqual(result["roles"][0]["relevanceStatus"], "direct")

    def test_title_only_match_is_insufficient(self):
        result = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [role("Flutter Developer", "Flutter Developer at Acme 2020 - 2022.")],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "insufficient_evidence")

    def test_global_skills_are_not_used_as_employment_evidence(self):
        candidate = role(
            "Sales Executive",
            "Sales Executive at Acme 2020 - 2022. Lead generation and client acquisition.",
        )
        candidate["globalSkills"] = ["Flutter"]
        result = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [candidate],
            ["Flutter"],
        )
        self.assertNotIn("Flutter", result["roles"][0]["matchedJobRequirements"])
        self.assertNotEqual(result["roles"][0]["relevanceStatus"], "direct")

    def test_overlapping_dated_roles_are_not_double_counted(self):
        result = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [
                role(
                    "Flutter Developer",
                    "Flutter Developer 2020 - 2022. "
                    "Build applications with Flutter and maintain code.",
                ),
                role(
                    "Software Developer",
                    "Software Developer 2021 - 2023. "
                    "Build applications with Flutter and maintain code.",
                ),
            ],
            ["Flutter"],
        )
        self.assertEqual(result["totalDirectRelevantMonths"], 36)

    def test_concurrent_direct_experience_takes_priority_over_transferable(self):
        result = analyze(
            "Mechanical Engineer",
            "CAD design and manage project budgets.",
            [
                role(
                    "Mechanical Engineer",
                    "Mechanical Engineer 2020 - 2022. CAD design.",
                ),
                role(
                    "Accountant",
                    "Accountant 2020 - 2022. Manage project budgets.",
                ),
            ],
            ["CAD"],
        )
        statuses = {item["relevanceStatus"] for item in result["roles"]}
        self.assertIn("direct", statuses)
        self.assertIn("transferable", statuses)
        self.assertEqual(result["totalDirectRelevantMonths"], 24)
        self.assertEqual(result["totalTransferableMonths"], 0)

    def test_current_employment_and_internships_keep_explicit_indicators(self):
        current = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [role(
                "Flutter Developer",
                "Flutter Developer Jan 2022 - Present. "
                "Build applications with Flutter and maintain code.",
                current=True,
            )],
            ["Flutter"],
        )
        internship = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [role(
                "Software Engineering Intern",
                "Software Engineering Intern Jan 2022 - Present. "
                "Build applications with Flutter and maintain code.",
                current=True,
                internship=True,
            )],
            ["Flutter"],
        )
        self.assertTrue(current["roles"][0]["dateEvidence"]["current"])
        self.assertGreater(current["totalDirectRelevantMonths"], 0)
        self.assertTrue(internship["roles"][0]["isInternship"])

    def test_missing_ambiguous_and_undated_duration_evidence_needs_review(self):
        missing = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [role(
                "Flutter Developer",
                "Flutter Developer at Acme. Build applications with Flutter. 2 years experience.",
            )],
            ["Flutter"],
        )
        ambiguous = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [role(
                "Flutter Developer",
                "Flutter Developer 2020 - 2021 and 2022 - 2023. "
                "Build applications with Flutter.",
            )],
            ["Flutter"],
        )
        self.assertEqual(missing["totalDirectRelevantMonths"], 0)
        self.assertEqual(missing["status"], "needs_review")
        self.assertEqual(
            ambiguous["roles"][0]["dateVerificationStatus"], "ambiguous_dates"
        )
        self.assertEqual(
            ambiguous["roles"][0]["durationVerificationStatus"], "needs_review"
        )

    def test_undated_unrelated_employment_is_still_marked_for_duration_review(self):
        result = analyze(
            "Flutter Developer",
            "Build applications with Flutter.",
            [role(
                "Sales Executive",
                "Sales Executive. Lead generation and client acquisition.",
            )],
            ["Flutter"],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "unrelated")
        self.assertEqual(
            result["roles"][0]["durationVerificationStatus"], "needs_review"
        )

    def test_transferable_experience_is_not_converted_to_direct_years(self):
        result = analyze(
            "Mechanical Engineer",
            "CAD design and manage project budgets.",
            [role(
                "Accountant",
                "Accountant 2020 - 2022. Manage project budgets.",
            )],
            ["CAD"],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "transferable")
        self.assertEqual(result["totalDirectRelevantMonths"], 0)
        self.assertEqual(result["totalTransferableMonths"], 24)

    def test_unsupported_requirements_and_missing_role_evidence_do_not_match(self):
        result = analyze(
            "Unlisted Specialist",
            "Perform highly specialized work.",
            [role("Unlisted Specialist", "Unlisted Specialist at Acme 2020 - 2022.")],
            ["Unlisted proprietary tool"],
        )
        self.assertEqual(result["roles"][0]["relevanceStatus"], "insufficient_evidence")
        self.assertEqual(result["roles"][0]["matchedJobRequirements"], [])

    def test_empty_evidence_does_not_create_employment_entries(self):
        result = analyze("Nurse", "Patient care.", [])
        self.assertEqual(result["roles"], [])
        self.assertEqual(result["totalDirectRelevantMonths"], 0)

    def test_same_job_requirements_are_applied_independently_per_candidate(self):
        candidate_evidence = [
            [
                role(
                    "Flutter Developer",
                    "Flutter Developer 2020 - 2022. "
                    "Build applications with Flutter and maintain code.",
                )
            ],
            [
                role(
                    "Sales Executive",
                    "Sales Executive 2020 - 2022. "
                    "Lead generation and client acquisition.",
                )
            ],
        ]
        results = [
            analyze(
                "Flutter Developer",
                "Build applications with Flutter.",
                evidence,
                ["Flutter"],
                "2 years",
            )
            for evidence in candidate_evidence
        ]
        self.assertEqual(
            [result["experienceRequirement"] for result in results],
            ["2 years", "2 years"],
        )
        self.assertEqual(
            [result["roles"][0]["relevanceStatus"] for result in results],
            ["direct", "unrelated"],
        )


if __name__ == "__main__":
    unittest.main()
