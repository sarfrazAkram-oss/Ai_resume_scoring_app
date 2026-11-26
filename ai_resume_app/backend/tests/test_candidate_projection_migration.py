import unittest
from types import SimpleNamespace

from scripts.migrate_candidate_projections import (
    audit_applications,
    build_candidate_projection,
)


class CandidateProjectionMigrationTests(unittest.TestCase):
    def test_projection_excludes_private_scoring_and_storage_fields(self) -> None:
        projection = build_candidate_projection(
            {
                "jobId": "job-1",
                "jobTitle": "Flutter Developer",
                "recruiterId": "recruiter-1",
                "candidateId": "candidate-1",
                "candidateName": "Candidate",
                "resumeFileName": "resume.pdf",
                "resumeStoragePath": "private/path",
                "status": "Rejected",
                "score": 40,
                "scoreBreakdown": {"skillsScore": 20},
                "scoringHistory": [{"score": 40}],
            }
        )

        self.assertEqual(projection["status"], "Rejected")
        self.assertFalse(projection["scoreShared"])
        self.assertNotIn("score", projection)
        self.assertNotIn("scoreBreakdown", projection)
        self.assertNotIn("scoringHistory", projection)
        self.assertNotIn("resumeStoragePath", projection)

    def test_audit_counts_missing_existing_and_ineligible_records(self) -> None:
        applications = [
            SimpleNamespace(
                id="existing",
                to_dict=lambda: {
                    "candidateId": "candidate-1",
                    "recruiterId": "recruiter-1",
                    "jobId": "job-1",
                },
            ),
            SimpleNamespace(
                id="eligible",
                to_dict=lambda: {
                    "candidateId": "candidate-2",
                    "recruiterId": "recruiter-2",
                    "jobId": "job-2",
                },
            ),
            SimpleNamespace(id="ineligible", to_dict=lambda: {"jobId": "job-3"}),
        ]

        summary = audit_applications(applications, {"existing": object()})

        self.assertEqual(
            summary,
            {
                "examined": 3,
                "missing": 2,
                "skipped": 1,
                "eligible": 1,
                "eligibleIds": ["eligible"],
            },
        )

    def test_projection_migration_is_retry_safe_by_skipping_existing_ids(self) -> None:
        application = SimpleNamespace(
            id="application-1",
            to_dict=lambda: {
                "candidateId": "candidate-1",
                "recruiterId": "recruiter-1",
                "jobId": "job-1",
            },
        )

        first = audit_applications([application], {})
        second = audit_applications([application], {"application-1": object()})

        self.assertEqual(first["eligible"], 1)
        self.assertEqual(second["eligible"], 0)
        self.assertEqual(second["skipped"], 1)


if __name__ == "__main__":
    unittest.main()
