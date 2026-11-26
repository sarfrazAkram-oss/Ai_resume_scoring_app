import copy
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app, admin_firestore


class FakeSnapshot:
    def __init__(self, reference: "FakeDocument") -> None:
        self.reference = reference

    @property
    def exists(self) -> bool:
        return self.reference.data is not None

    def to_dict(self) -> dict | None:
        return copy.deepcopy(self.reference.data)


class FakeDocument:
    def __init__(
        self,
        document_id: str,
        collection_name: str,
        data: dict | None = None,
    ) -> None:
        self.id = document_id
        self.collection_name = collection_name
        self.data = copy.deepcopy(data)

    def get(self, transaction: "FakeTransaction | None" = None) -> FakeSnapshot:
        if transaction is not None:
            transaction.read(self)
        return FakeSnapshot(self)


class FakeCollection:
    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name
        self.documents: dict[str, FakeDocument] = {}

    def document(self, document_id: str) -> FakeDocument:
        return self.documents.setdefault(
            document_id,
            FakeDocument(document_id, self.collection_name),
        )


class FakeTransaction:
    def __init__(self) -> None:
        self.reads: list[FakeDocument] = []
        self.operations: list[tuple[str, FakeDocument, dict]] = []

    def read(self, reference: FakeDocument) -> None:
        self.reads.append(reference)

    def update(self, reference: FakeDocument, data: dict) -> None:
        self.operations.append(("update", reference, copy.deepcopy(data)))

    def create(self, reference: FakeDocument, data: dict) -> None:
        self.operations.append(("create", reference, copy.deepcopy(data)))

    def commit(self) -> None:
        for operation, reference, _ in self.operations:
            if operation == "update" and reference.data is None:
                raise AssertionError("transaction attempted to update a missing document")
            if operation == "create" and reference.data is not None:
                raise AssertionError("transaction attempted to create an existing document")
        for operation, reference, data in self.operations:
            if operation == "create":
                reference.data = data
            else:
                reference.data.update(data)


class FakeFirestore:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}
        self.transactions: list[FakeTransaction] = []

    def collection(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection(name))

    def transaction(self) -> FakeTransaction:
        transaction = FakeTransaction()
        self.transactions.append(transaction)
        return transaction


def _commit_fake_transaction(function):
    def run(transaction: FakeTransaction):
        result = function(transaction)
        transaction.commit()
        return result

    return run


class RecruiterApplicationActionTests(unittest.TestCase):
    application_id = "application-1"
    original_score = 82.5
    original_breakdown = {
        "skillsScore": 33.0,
        "experienceScore": 20.0,
        "educationScore": 16.0,
        "practicalWorkScore": 13.5,
        "finalScore": 82.5,
    }

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.firestore = FakeFirestore()
        self.firestore.collection("jobs").document("job-1").data = {
            "createdBy": "recruiter-1",
            "title": "Flutter Engineer",
        }
        self.firestore.collection("applications").document(
            self.application_id
        ).data = {
            "jobId": "job-1",
            "jobTitle": "Flutter Engineer",
            "recruiterId": "recruiter-1",
            "candidateId": "candidate-1",
            "status": "Pending",
            "score": self.original_score,
            "scoreBreakdown": copy.deepcopy(self.original_breakdown),
            "scoreShared": False,
        }
        self.firestore.collection("candidateApplications").document(
            self.application_id
        ).data = {
            "jobId": "job-1",
            "jobTitle": "Flutter Engineer",
            "recruiterId": "recruiter-1",
            "candidateId": "candidate-1",
            "status": "Pending",
            "scoreShared": False,
        }
        self.firestore_patcher = patch(
            "app.main.get_firestore_client",
            return_value=self.firestore,
        )
        self.firestore_patcher.start()
        self.addCleanup(self.firestore_patcher.stop)

        self.auth_mock = patch(
            "app.main.verify_firebase_token",
            return_value="recruiter-1",
        )
        self.mock_verify_token = self.auth_mock.start()
        self.addCleanup(self.auth_mock.stop)

        self.transaction_patcher = patch(
            "app.main.admin_firestore.transactional",
            side_effect=_commit_fake_transaction,
        )
        self.transaction_patcher.start()
        self.addCleanup(self.transaction_patcher.stop)

    def _post(self, path: str) -> object:
        return self.client.post(
            path,
            json={"applicationId": self.application_id},
            headers={"Authorization": "Bearer verified-recruiter-token"},
        )

    def _saved_notifications(self) -> list[FakeDocument]:
        return [
            document
            for document in self.firestore.collection(
                "candidateNotifications"
            ).documents.values()
            if document.data is not None
        ]

    def test_authorized_recruiter_shares_existing_score_without_changing_it(self) -> None:
        response = self._post("/share-application-score")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "applicationId": self.application_id,
                "scoreShared": True,
            },
        )
        application = self.firestore.collection("applications").document(
            self.application_id
        ).data
        projection = self.firestore.collection("candidateApplications").document(
            self.application_id
        ).data
        self.assertEqual(application["score"], self.original_score)
        self.assertEqual(application["scoreBreakdown"], self.original_breakdown)
        self.assertTrue(application["scoreShared"])
        self.assertEqual(projection["score"], self.original_score)
        self.assertEqual(projection["scoreBreakdown"], self.original_breakdown)
        self.assertTrue(projection["scoreShared"])
        self.mock_verify_token.assert_called_once_with("Bearer verified-recruiter-token")

    def test_repeated_score_share_is_idempotent(self) -> None:
        first_response = self._post("/share-application-score")
        second_response = self._post("/share-application-score")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        application = self.firestore.collection("applications").document(
            self.application_id
        ).data
        projection = self.firestore.collection("candidateApplications").document(
            self.application_id
        ).data
        self.assertEqual(application["score"], self.original_score)
        self.assertEqual(projection["score"], self.original_score)
        self.assertTrue(application["scoreShared"])
        self.assertTrue(projection["scoreShared"])

    def test_unauthorized_recruiter_cannot_share_another_recruiters_score(self) -> None:
        self.mock_verify_token.return_value = "recruiter-2"

        response = self._post("/share-application-score")

        self.assertEqual(response.status_code, 403)
        application = self.firestore.collection("applications").document(
            self.application_id
        ).data
        projection = self.firestore.collection("candidateApplications").document(
            self.application_id
        ).data
        self.assertFalse(application["scoreShared"])
        self.assertNotIn("score", projection)
        self.assertEqual(self.firestore.transactions[-1].operations, [])

    def test_score_share_rejects_mismatched_candidate_projection(self) -> None:
        projection = self.firestore.collection("candidateApplications").document(
            self.application_id
        )
        projection.data["candidateId"] = "candidate-2"

        response = self._post("/share-application-score")

        self.assertEqual(response.status_code, 409)
        self.assertNotIn("score", projection.data)
        self.assertFalse(
            self.firestore.collection("applications")
            .document(self.application_id)
            .data["scoreShared"]
        )

    def test_score_share_rejects_mismatched_job_projection(self) -> None:
        projection = self.firestore.collection("candidateApplications").document(
            self.application_id
        )
        projection.data["jobId"] = "job-2"

        response = self._post("/share-application-score")

        self.assertEqual(response.status_code, 409)
        self.assertNotIn("score", projection.data)
        self.assertFalse(
            self.firestore.collection("applications")
            .document(self.application_id)
            .data["scoreShared"]
        )

    def test_authorized_recruiter_rejects_and_notifies_candidate_atomically(self) -> None:
        projection = self.firestore.collection("candidateApplications").document(
            self.application_id
        )
        projection.data["score"] = 17.0
        projection.data["scoreBreakdown"] = {"finalScore": 17.0}

        response = self._post("/reject-application")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "Rejected")
        self.assertTrue(response.json()["notificationSaved"])
        application = self.firestore.collection("applications").document(
            self.application_id
        ).data
        projection_data = projection.data
        notifications = self.firestore.collection("candidateNotifications").documents
        self.assertEqual(application["status"], "Rejected")
        self.assertEqual(projection_data["status"], "Rejected")
        self.assertEqual(application["score"], self.original_score)
        self.assertEqual(application["scoreBreakdown"], self.original_breakdown)
        self.assertFalse(application["scoreShared"])
        self.assertFalse(projection_data["scoreShared"])
        self.assertEqual(projection_data["score"], 17.0)
        self.assertEqual(projection_data["scoreBreakdown"], {"finalScore": 17.0})
        self.assertEqual(len(notifications), 1)
        notification = next(iter(notifications.values())).data
        self.assertEqual(notification["candidateId"], "candidate-1")
        self.assertEqual(notification["applicationId"], self.application_id)
        self.assertEqual(notification["jobId"], "job-1")
        self.assertEqual(notification["type"], "rejection")
        self.assertIn("Flutter Engineer", notification["title"])
        self.assertIn("Flutter Engineer", notification["message"])
        self.assertFalse(notification["read"])
        self.assertIs(notification["createdAt"], admin_firestore.SERVER_TIMESTAMP)
        self.mock_verify_token.assert_called_once_with("Bearer verified-recruiter-token")

    def test_duplicate_rejection_reuses_one_notification(self) -> None:
        first_response = self._post("/reject-application")
        notifications = self.firestore.collection("candidateNotifications")
        notification_id, notification = next(iter(notifications.documents.items()))
        original_notification = copy.deepcopy(notification.data)

        second_response = self._post("/reject-application")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.json()["notificationId"], notification_id)
        self.assertEqual(len(notifications.documents), 1)
        self.assertEqual(notification.data, original_notification)

    def test_unauthorized_recruiter_cannot_reject_or_notify(self) -> None:
        self.mock_verify_token.return_value = "recruiter-2"

        response = self._post("/reject-application")

        self.assertEqual(response.status_code, 403)
        application = self.firestore.collection("applications").document(
            self.application_id
        ).data
        projection = self.firestore.collection("candidateApplications").document(
            self.application_id
        ).data
        self.assertEqual(application["status"], "Pending")
        self.assertEqual(projection["status"], "Pending")
        self.assertEqual(self._saved_notifications(), [])
        self.assertEqual(self.firestore.transactions[-1].operations, [])

    def test_rejection_requires_application_job_ownership_to_match(self) -> None:
        self.firestore.collection("jobs").document("job-1").data["createdBy"] = (
            "recruiter-2"
        )

        response = self._post("/reject-application")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self._saved_notifications(), [])

    def test_share_requires_a_saved_score_and_breakdown(self) -> None:
        application = self.firestore.collection("applications").document(
            self.application_id
        )
        application.data["score"] = None

        response = self._post("/share-application-score")

        self.assertEqual(response.status_code, 409)
        self.assertFalse(application.data["scoreShared"])
        self.assertNotIn(
            "score",
            self.firestore.collection("candidateApplications")
            .document(self.application_id)
            .data,
        )

    def test_share_endpoint_rejects_client_supplied_score_values(self) -> None:
        response = self.client.post(
            "/share-application-score",
            json={
                "applicationId": self.application_id,
                "score": 100,
                "scoreBreakdown": {"finalScore": 100},
            },
            headers={"Authorization": "Bearer verified-recruiter-token"},
        )

        self.assertEqual(response.status_code, 422)
        application = self.firestore.collection("applications").document(
            self.application_id
        ).data
        self.assertEqual(application["score"], self.original_score)
        self.assertFalse(application["scoreShared"])

    def test_action_endpoints_reject_invalid_firebase_tokens(self) -> None:
        self.mock_verify_token.side_effect = HTTPException(
            status_code=401,
            detail="Invalid Firebase token",
        )

        share_response = self._post("/share-application-score")
        reject_response = self._post("/reject-application")

        self.assertEqual(share_response.status_code, 401)
        self.assertEqual(reject_response.status_code, 401)
        self.assertEqual(
            self.firestore.collection("candidateNotifications").documents,
            {},
        )


if __name__ == "__main__":
    unittest.main()
