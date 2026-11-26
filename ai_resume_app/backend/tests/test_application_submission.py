import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from google.api_core.exceptions import AlreadyExists

from app.main import app


class FakeDocument:
    def __init__(
        self,
        document_id: str,
        data: dict | None = None,
        collection_name: str = "",
    ) -> None:
        self.id = document_id
        self.collection_name = collection_name
        self._data = data
        self.exists = data is not None

    def get(self) -> "FakeDocument":
        return self

    def to_dict(self) -> dict | None:
        return self._data


class FakeCollection:
    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name
        self.documents: dict[str, FakeDocument] = {}
        self.query_matches: list[object] = []
        self.filters: list[tuple[object, ...]] = []

    def document(self, document_id: str) -> FakeDocument:
        return self.documents.setdefault(
            document_id,
            FakeDocument(document_id, collection_name=self.collection_name),
        )

    def where(self, *args: object, **_kwargs: object) -> "FakeCollection":
        self.filters.append(args)
        return self

    def limit(self, _count: int) -> "FakeCollection":
        return self

    def get(self) -> list[object]:
        return self.query_matches


class FakeBatch:
    def __init__(self) -> None:
        self.creates: list[tuple[FakeDocument, dict]] = []
        self.commit_error: Exception | None = None

    def create(self, reference: FakeDocument, data: dict) -> None:
        self.creates.append((reference, data))

    def commit(self) -> None:
        if self.commit_error is not None:
            raise self.commit_error


class FakeFirestore:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}
        self.write_batch = FakeBatch()

    def collection(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection(name))

    def batch(self) -> FakeBatch:
        return self.write_batch


class ApplicationSubmissionEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.firestore = FakeFirestore()
        self.firestore.collection("jobs").documents["job-1"] = FakeDocument(
            "job-1",
            {
                "createdBy": "recruiter-1",
                "title": "Flutter Developer",
                "companyName": "Example Co",
                "status": "active",
            },
            collection_name="jobs",
        )
        self.firestore_patch = patch(
            "app.main.get_firestore_client",
            return_value=self.firestore,
        )
        self.firestore_patch.start()
        self.addCleanup(self.firestore_patch.stop)
        self.auth_patch = patch(
            "app.main.verify_firebase_token",
            return_value="verified-candidate",
        )
        self.auth_patch.start()
        self.addCleanup(self.auth_patch.stop)

    def test_duplicate_preflight_uses_verified_uid(self) -> None:
        response = self.client.post(
            "/application-duplicate-check",
            json={"jobId": "job-1", "candidateId": "untrusted-client-uid"},
            headers={"Authorization": "Bearer verified-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"duplicate": False})
        self.assertIn(
            ("candidateId", "==", "verified-candidate"),
            self.firestore.collection("applications").filters,
        )

    def test_submit_atomically_creates_same_id_documents_and_unique_lock(self) -> None:
        response = self.client.post(
            "/submit-application",
            json={
                "applicationId": "application-1",
                "jobId": "job-1",
                "resumeFileName": "resume.pdf",
                "resumeStoragePath": (
                    "verified-candidate/job-1/application-1.pdf"
                ),
                "candidateName": "Candidate",
                "candidateEmail": "candidate@example.com",
                "candidateId": "untrusted-client-uid",
            },
            headers={"Authorization": "Bearer verified-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"applicationId": "application-1"})
        self.assertEqual(len(self.firestore.write_batch.creates), 3)

        private_reference, private_data = next(
            (reference, data)
            for reference, data in self.firestore.write_batch.creates
            if reference.collection_name == "applications"
        )
        projection_reference, projection = next(
            (reference, data)
            for reference, data in self.firestore.write_batch.creates
            if reference.collection_name == "candidateApplications"
        )
        self.assertEqual(private_reference.id, "application-1")
        self.assertEqual(projection_reference.id, private_reference.id)
        self.assertEqual(private_data["candidateId"], "verified-candidate")
        self.assertEqual(private_data["recruiterId"], "recruiter-1")
        self.assertEqual(
            private_data["resumeStoragePath"],
            "verified-candidate/job-1/application-1.pdf",
        )
        self.assertIsNotNone(private_data["appliedAt"])
        self.assertEqual(
            {
                key: value
                for key, value in private_data.items()
                if key in {
                    "jobId",
                    "jobTitle",
                    "recruiterId",
                    "candidateId",
                    "candidateName",
                    "resumeFileName",
                    "appliedAt",
                    "status",
                    "scoreShared",
                }
            },
            {
                "jobId": "job-1",
                "jobTitle": "Flutter Developer",
                "recruiterId": "recruiter-1",
                "candidateId": "verified-candidate",
                "candidateName": "Candidate",
                "resumeFileName": "resume.pdf",
                "appliedAt": private_data["appliedAt"],
                "status": "Pending",
                "scoreShared": False,
            },
        )
        self.assertEqual(
            set(projection),
            {
                "jobId",
                "jobTitle",
                "recruiterId",
                "candidateId",
                "candidateName",
                "resumeFileName",
                "appliedAt",
                "status",
                "scoreShared",
            },
        )
        self.assertEqual(projection["candidateId"], "verified-candidate")

    def test_existing_private_application_is_rejected_without_writes(self) -> None:
        self.firestore.collection("applications").query_matches = [object()]

        response = self.client.post(
            "/submit-application",
            json={
                "applicationId": "application-2",
                "jobId": "job-1",
                "resumeFileName": "resume.pdf",
                "resumeStoragePath": (
                    "verified-candidate/job-1/application-2.pdf"
                ),
                "candidateName": "Candidate",
                "candidateEmail": "candidate@example.com",
            },
            headers={"Authorization": "Bearer verified-token"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.firestore.write_batch.creates, [])

    def test_concurrent_unique_lock_conflict_rejects_submission(self) -> None:
        self.firestore.write_batch.commit_error = AlreadyExists("already exists")

        response = self.client.post(
            "/submit-application",
            json={
                "applicationId": "application-3",
                "jobId": "job-1",
                "resumeFileName": "resume.pdf",
                "resumeStoragePath": (
                    "verified-candidate/job-1/application-3.pdf"
                ),
                "candidateName": "Candidate",
                "candidateEmail": "candidate@example.com",
            },
            headers={"Authorization": "Bearer verified-token"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(self.firestore.write_batch.creates), 3)


if __name__ == "__main__":
    unittest.main()
