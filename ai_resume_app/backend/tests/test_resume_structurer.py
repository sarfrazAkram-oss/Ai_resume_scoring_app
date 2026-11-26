import unittest

from app.services.education_scorer import score_education
from app.services.resume_scorer import score_experience, score_skills
from app.services.resume_structurer import extract_structured_information


class ResumeStructurerTests(unittest.TestCase):
    def test_skill_aliases_are_normalized_and_substrings_are_not_matched(self) -> None:
        result = extract_structured_information(
            "SKILLS\nJS\nJavaScript\nJava\n"
        )
        self.assertEqual(result["skills"], ["JavaScript", "Java"])

    def test_casual_skill_mentions_need_skill_or_usage_evidence(self) -> None:
        result = extract_structured_information(
            "SUMMARY\nInterested in Python and JavaScript.\n"
            "EXPERIENCE\nBuilt a service using Python.\n"
        )
        self.assertEqual(result["skills"], ["Python"])

    def test_provider_is_extracted_from_explicit_usage_evidence(self) -> None:
        result = extract_structured_information(
            "EXPERIENCE\n"
            "- Implemented state management and data persistence using provider and SQLite.\n"
        )

        self.assertIn("Provider", result["skills"])

    def test_computer_skills_heading_extracts_terms_from_real_resume_layout(self) -> None:
        result = extract_structured_information(
            "COMPUTER SKILLS\nEPIC, Microsoft Word\n"
            "EXPERIENCE\nMaintained patient records with EPIC.\n"
        )
        normalized = {skill.casefold() for skill in result["skills"]}
        self.assertIn("epic", normalized)
        self.assertIn("microsoft word", normalized)
        self.assertNotIn("computer skills", normalized)

    def test_professional_skill_aliases_are_canonicalized(self) -> None:
        result = extract_structured_information(
            "SKILLS\nHR, CRM, SEO, EMR, CAD\n"
        )
        self.assertEqual(
            result["skills"],
            [
                "Human Resources",
                "Customer Relationship Management",
                "Search Engine Optimization",
                "Electronic Medical Records",
                "Computer-Aided Design",
            ],
        )
        scored = score_skills(
            result["skills"],
            ["HR", "customer relationship management",
             "SEO", "electronic medical records", "computer aided design"],
        )
        self.assertEqual(scored["matchedSkillsCount"], 5)

    def test_professional_aliases_require_whole_skill_tokens(self) -> None:
        result = extract_structured_information(
            "SUMMARY\nThe workflow improved customer relationship management "
            "and supports HR, CRM, SEO, EMR, and CAD terminology.\n"
        )
        self.assertEqual(result["skills"], [])

    def test_relevant_projects_are_split_into_individual_bullets(self) -> None:
        result = extract_structured_information(
            "RELEVANT PROJECTS\n"
            "- Resume Matcher: Built using Python.\n"
            "- Job Tracker: Developed with React.\n"
            "CERTIFICATIONS\nAWS Certified Developer\n"
        )
        projects = result["projects"]
        self.assertEqual(len(projects), 2)
        self.assertIn("Resume Matcher", projects[0]["text"])
        self.assertIn("Job Tracker", projects[1]["text"])
        self.assertNotIn("certification", " ".join(
            project["text"].casefold() for project in projects
        ))

    def test_project_title_lines_split_without_bullets(self) -> None:
        result = extract_structured_information(
            "PROJECTS\n"
            "Project 1: Resume Matcher using Python\n"
            "Project 2: Job Tracker using React\n"
        )
        self.assertEqual(len(result["projects"]), 2)

    def test_unheaded_casual_project_mention_is_not_structured_as_project(self) -> None:
        result = extract_structured_information(
            "SUMMARY\nI built projects using Python and React.\n"
        )
        self.assertEqual(result["projects"], [])

    def test_education_and_project_dates_do_not_become_experience(self) -> None:
        result = extract_structured_information(
            "EDUCATION\nBSCS 2021 - 2025\n"
            "PROJECTS\nPersonal project 2022 - 2024\n"
            "EXPERIENCE\nSoftware Engineer at Example Co. 2020 - 2022\n"
        )
        experience = result["experience"]
        self.assertEqual(len(experience), 1)
        score = score_experience(experience, "2 years")
        self.assertEqual(score["candidateYears"], 2.0)

    def test_employment_evidence_is_additive_and_keeps_role_details(self) -> None:
        structured = extract_structured_information(
            "SKILLS\nFlutter\n"
            "EXPERIENCE\n"
            "Flutter Developer at Acme\n"
            "Jan 2020 - Present\n"
            "- Built Flutter applications for customers.\n"
            "- Used Python and Docker.\n"
        )

        self.assertEqual(structured["experience"], [
            {"text": "Flutter Developer at Acme"},
            {"text": "Jan 2020 - Present"},
            {"text": "Built Flutter applications for customers."},
            {"text": "Used Python and Docker."},
        ])
        [evidence] = structured["employmentEvidence"]
        self.assertEqual(evidence["title"], "Flutter Developer")
        self.assertEqual(evidence["employer"], "Acme")
        self.assertEqual(evidence["startDateEvidence"], "Jan 2020")
        self.assertEqual(evidence["endDateEvidence"], "Present")
        self.assertTrue(evidence["isCurrent"])
        self.assertTrue(evidence["sourceText"])
        self.assertIn("Built Flutter applications", evidence["sourceText"])
        self.assertIn("Docker", evidence["technologiesAndTools"])
        self.assertEqual(evidence["extractionConfidence"], "high")

    def test_ambiguous_employment_is_preserved_without_invented_fields(self) -> None:
        source = (
            "EXPERIENCE\n"
            "Worked across several teams and technologies without clear role boundaries.\n"
        )
        [evidence] = extract_structured_information(source)["employmentEvidence"]
        self.assertIsNone(evidence["title"])
        self.assertIsNone(evidence["employer"])
        self.assertIsNone(evidence["startDateEvidence"])
        self.assertEqual(evidence["extractionConfidence"], "ambiguous")
        self.assertEqual(
            evidence["sourceText"],
            "Worked across several teams and technologies without clear role boundaries.",
        )

    def test_live_scoring_mode_skips_new_employment_evidence(self) -> None:
        structured = extract_structured_information(
            "EXPERIENCE\nFlutter Developer at Acme 2020 - 2022\n",
            include_employment_evidence=False,
        )
        self.assertEqual(
            set(structured),
            {"skills", "experience", "education", "projects"},
        )
        self.assertEqual(
            structured["experience"],
            [{"text": "Flutter Developer at Acme 2020 - 2022"}],
        )

    def test_internship_indicator_requires_explicit_title_evidence(self) -> None:
        [evidence] = extract_structured_information(
            "INTERNSHIP\nSoftware Engineering Intern at Acme 2022 - 2023\n"
        )["employmentEvidence"]
        self.assertTrue(evidence["isInternship"])

    def test_multiple_employment_entries_keep_their_own_evidence(self) -> None:
        structured = extract_structured_information(
            "EXPERIENCE\n"
            "Software Engineer at Acme\n2020 - 2022\n"
            "- Build applications with Python.\n"
            "Sales Executive at Northwind\n2022 - 2024\n"
            "- Lead generation and client acquisition.\n"
        )
        entries = structured["employmentEvidence"]
        self.assertEqual(len(entries), 2)
        self.assertEqual([entry["title"] for entry in entries], [
            "Software Engineer", "Sales Executive",
        ])
        self.assertIn("Build applications", entries[0]["sourceText"])
        self.assertNotIn("Lead generation", entries[0]["sourceText"])
        self.assertIn("Lead generation", entries[1]["sourceText"])

    def test_multiple_qualifications_keep_their_own_fields(self) -> None:
        structured = extract_structured_information(
            "EDUCATION\nBSc in Arts; MSc in Computer Science\n"
        )
        result = score_education(
            structured["education"],
            "Master's degree in Computer Science",
        )
        self.assertEqual(result["candidateDegree"], "MSc")
        self.assertEqual(result["candidateLevel"], "master")
        self.assertEqual(result["candidateField"], "computer_science")
        self.assertEqual(result["educationScore"], 20.0)

    def test_plural_bachelors_and_masters_are_recognized(self) -> None:
        bachelors = score_education([{"text": "Bachelors"}], "Bachelors")
        masters = score_education([{"text": "Masters"}], "Masters")
        self.assertEqual(bachelors["candidateLevel"], "bachelor")
        self.assertEqual(masters["candidateLevel"], "master")


if __name__ == "__main__":
    unittest.main()
