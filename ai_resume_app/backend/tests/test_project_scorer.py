import unittest

from app.services.project_scorer import score_projects


class ProjectScorerTests(unittest.TestCase):
    def test_all_required_skills_evidenced(self) -> None:
        result = score_projects(
            [{"text": "Built a service using Flutter, Dart, and Firebase"}],
            "Flutter Developer",
            "Flutter, Dart, Firebase",
            "Build mobile applications",
        )
        self.assertEqual(
            result["matchedProjectSkills"], ["Flutter", "Dart", "Firebase"]
        )
        self.assertEqual(result["missingProjectSkills"], [])
        self.assertEqual(result["projectsScore"], 15.0)

    def test_partial_match_uses_required_skill_ratio(self) -> None:
        result = score_projects(
            [{"text": "Quran Learning App developed using Flutter, Dart and Firebase"}],
            "Flutter Developer",
            "Flutter, Dart, Firebase, REST API",
            "Build and maintain mobile applications.",
        )
        self.assertEqual(
            result["matchedProjectSkills"], ["Flutter", "Dart", "Firebase"]
        )
        self.assertEqual(result["missingProjectSkills"], ["REST API"])
        self.assertEqual(result["requiredSkillsCount"], 4)
        self.assertEqual(result["matchedSkillsCount"], 3)
        self.assertEqual(result["matchPercentage"], 75.0)
        self.assertEqual(result["projectsScore"], 11.25)

    def test_zero_project_match(self) -> None:
        result = score_projects(
            [{"text": "Created an online shop using Next.js"}],
            "Flutter Developer",
            "Flutter, Dart",
            "Build mobile applications",
        )
        self.assertEqual(result["matchedProjectSkills"], [])
        self.assertEqual(result["missingProjectSkills"], ["Flutter", "Dart"])
        self.assertEqual(result["matchPercentage"], 0.0)
        self.assertEqual(result["projectsScore"], 0.0)

    def test_empty_projects_score_zero_when_requirements_exist(self) -> None:
        result = score_projects([], "Developer", "Python", "Build software")
        self.assertEqual(result["projectsScore"], 0.0)
        self.assertEqual(result["status"], "scored")

    def test_empty_requirements_are_not_scored(self) -> None:
        for requirements in ("", " , ; \n", [], None):
            with self.subTest(requirements=requirements):
                result = score_projects(
                    [{"text": "A project using Python"}],
                    "Python Developer",
                    requirements,
                    "Python work",
                )
                self.assertIsNone(result["projectsScore"])
                self.assertIsNone(result["matchPercentage"])
                self.assertEqual(result["matchedProjectSkills"], [])
                self.assertEqual(result["missingProjectSkills"], [])
                self.assertEqual(
                    result["status"], "not_scored_no_project_requirements"
                )

    def test_same_skill_across_projects_counts_once(self) -> None:
        result = score_projects(
            [
                {"text": "Project A uses Flutter"},
                {"text": "Project B also uses Flutter"},
            ],
            "Flutter developer",
            "Flutter, Dart",
            "Build products",
        )
        self.assertEqual(result["matchedProjectSkills"], ["Flutter"])
        self.assertEqual(result["matchedSkillsCount"], 1)
        self.assertEqual(result["projectsScore"], 7.5)

    def test_aliases_match_using_existing_skill_aliases(self) -> None:
        result = score_projects(
            [{"text": "Created a NextJS shop and a ReactJS dashboard"}],
            "Frontend Engineer",
            "Next.js, React",
            "Build web interfaces",
        )
        self.assertEqual(result["matchedProjectSkills"], ["Next.js", "React"])
        self.assertEqual(result["projectsScore"], 15.0)

    def test_matching_is_case_insensitive(self) -> None:
        result = score_projects(
            [{"text": "FLUTTER and DART"}], "Developer", "Flutter, Dart", ""
        )
        self.assertEqual(result["matchedProjectSkills"], ["Flutter", "Dart"])
        self.assertEqual(result["projectsScore"], 15.0)

    def test_c_does_not_match_css(self) -> None:
        result = score_projects(
            [{"text": "Styled pages with CSS"}], "C Developer", "C", ""
        )
        self.assertEqual(result["matchedProjectSkills"], [])
        self.assertEqual(result["missingProjectSkills"], ["C"])

    def test_java_does_not_match_javascript(self) -> None:
        result = score_projects(
            [{"text": "Built frontend with JavaScript"}], "Java Developer", "Java", ""
        )
        self.assertEqual(result["matchedProjectSkills"], [])
        self.assertEqual(result["missingProjectSkills"], ["Java"])

    def test_distinct_projects_contribute_unique_requirements(self) -> None:
        result = score_projects(
            [
                {"text": "Mobile client developed with Flutter"},
                {"text": "Data service built with Dart and Firebase"},
            ],
            "Flutter Developer",
            "Flutter, Dart, Firebase, REST API",
            "Build mobile and API services",
        )
        self.assertEqual(
            result["matchedProjectSkills"], ["Flutter", "Dart", "Firebase"]
        )
        self.assertEqual(result["missingProjectSkills"], ["REST API"])
        self.assertEqual(result["projectsScore"], 11.25)

    def test_title_and_description_alone_do_not_award_points(self) -> None:
        result = score_projects(
            [{"text": "Developed an application system"}],
            "Flutter Developer",
            "Flutter, Dart",
            "Software developer application system projects",
        )
        self.assertEqual(result["projectsScore"], 0.0)
        self.assertEqual(result["matchedProjectSkills"], [])


if __name__ == "__main__":
    unittest.main()