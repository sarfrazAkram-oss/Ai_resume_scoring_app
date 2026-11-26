import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import (
    app,
    download_resume_for_scoring,
    initialize_firebase_admin,
    fetch_job_for_scoring,
    normalize_job_scoring_policy,
    persist_application_score,
    score_resume,
    verify_firebase_token,
)


class ScoreApplicationEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.scoring_status_patcher = patch("app.main.persist_scoring_status")
        self.mock_persist_scoring_status = self.scoring_status_patcher.start()
        self.addCleanup(self.scoring_status_patcher.stop)
        self.mock_firestore_client = Mock()
        self.firestore_client_patcher = patch(
            "app.main.get_firestore_client",
            return_value=self.mock_firestore_client,
        )
        self.firestore_client_patcher.start()
        self.addCleanup(self.firestore_client_patcher.stop)

    @patch(
        "app.main.extract_resume_text",
        return_value=(
            "docx",
            "EXPERIENCE\n"
            "Flutter Developer at Acme 2020 - 2022\n"
            "- Build applications with Flutter.\n",
        ),
    )
    def test_structured_extraction_endpoint_serializes_employment_evidence(
        self,
        _mock_extract: Mock,
    ) -> None:
        response = self.client.post(
            "/extract-resume-structured",
            files={"file": ("resume.docx", b"document bytes")},
        )

        self.assertEqual(response.status_code, 200)
        structured = response.json()["structured"]
        self.assertEqual(structured["experience"][0]["text"],
                         "Flutter Developer at Acme 2020 - 2022")
        self.assertEqual(
            structured["employmentEvidence"][0]["title"],
            "Flutter Developer",
        )

    @patch.dict(
        "os.environ",
        {"FIREBASE_SERVICE_ACCOUNT_JSON": '{"type":"service_account"}', "FIREBASE_PROJECT_ID": "test-project"},
        clear=True,
    )
    @patch("app.main.credentials.Certificate")
    @patch("app.main.firebase_admin.initialize_app")
    @patch("app.main.firebase_admin.get_app", side_effect=ValueError("not initialized"))
    def test_firebase_admin_initializes_from_configured_service_account(
        self,
        _mock_get_app: Mock,
        mock_initialize: Mock,
        mock_certificate: Mock,
    ) -> None:
        initialize_firebase_admin()

        mock_certificate.assert_called_once_with({"type": "service_account"})
        mock_initialize.assert_called_once_with(
            mock_certificate.return_value,
            options={"projectId": "test-project"},
        )

    @patch("app.main.verify_firebase_token")
    def test_missing_authorization_header(self, mock_verify: Mock) -> None:
        mock_verify.side_effect = HTTPException(status_code=401, detail="Missing bearer token")
        response = self.client.post("/score-application", json={"applicationId": "app-1"})
        self.assertEqual(response.status_code, 401)

    @patch("app.main.verify_firebase_token")
    def test_invalid_firebase_token(self, mock_verify: Mock) -> None:
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid Firebase token")
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer invalid-token"},
        )
        self.assertEqual(response.status_code, 401)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    def test_application_not_found(self, mock_fetch: Mock, _mock_verify: Mock) -> None:
        mock_fetch.side_effect = HTTPException(status_code=404, detail="Application not found")
        response = self.client.post(
            "/score-application",
            json={"applicationId": "missing-app"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 404)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    def test_existing_score_requires_explicit_rescore_confirmation(
        self,
        mock_fetch: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch.return_value = {
            "score": 53.33,
            "candidateId": "candidate-1",
        }

        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "******"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("explicit confirmation", response.json()["detail"])
        self.mock_persist_scoring_status.assert_not_called()

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch(
        "app.main.score_application_for_application",
        return_value={
            "applicationId": "app-1",
            "score": 80.0,
            "scoreBreakdown": {},
            "scoringStatus": "scored",
            "scoredAt": None,
            "scoringModelVersion": 3,
        },
    )
    def test_endpoint_passes_explicit_rescore_confirmation(
        self,
        mock_score: Mock,
        _mock_verify: Mock,
    ) -> None:
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1", "confirmRescore": True},
            headers={"Authorization": "******"},
        )

        self.assertEqual(response.status_code, 200)
        mock_score.assert_called_once_with(
            "app-1",
            "candidate-1",
            confirm_rescore=True,
        )

    @patch("app.main.verify_firebase_token", return_value="candidate-2")
    @patch("app.main.fetch_application_for_scoring")
    def test_authenticated_uid_mismatch(self, mock_fetch: Mock, _mock_verify: Mock) -> None:
        mock_fetch.side_effect = HTTPException(status_code=403, detail="Application ownership mismatch")
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 403)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    @patch("app.main.fetch_job_for_scoring")
    def test_job_not_found(
        self,
        mock_fetch_job: Mock,
        mock_fetch_application: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch_application.return_value = {"jobId": "job-9", "candidateId": "candidate-1"}
        mock_fetch_job.side_effect = HTTPException(status_code=404, detail="Job not found")
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 404)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    @patch("app.main.fetch_job_for_scoring")
    @patch("app.main.download_resume_for_scoring")
    def test_missing_resume_storage_path(
        self,
        _mock_download: Mock,
        _mock_fetch_job: Mock,
        mock_fetch_application: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch_application.return_value = {
            "jobId": "job-1",
            "candidateId": "candidate-1",
            "resumeStoragePath": "",
            "resumeFileName": "cv.pdf",
        }
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 400)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    @patch("app.main.fetch_job_for_scoring")
    @patch("app.main.download_resume_for_scoring")
    def test_resume_download_failure(
        self,
        mock_download: Mock,
        _mock_fetch_job: Mock,
        mock_fetch_application: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch_application.return_value = {
            "jobId": "job-1",
            "candidateId": "candidate-1",
            "resumeStoragePath": "candidate/cv.pdf",
            "resumeFileName": "cv.pdf",
        }
        mock_download.side_effect = HTTPException(status_code=502, detail="Resume download failed")
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 502)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    @patch("app.main.fetch_job_for_scoring")
    @patch("app.main.download_resume_for_scoring")
    @patch("app.main.extract_resume_text")
    def test_extraction_failure(
        self,
        mock_extract: Mock,
        _mock_download: Mock,
        _mock_fetch_job: Mock,
        mock_fetch_application: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch_application.return_value = {
            "jobId": "job-1",
            "candidateId": "candidate-1",
            "resumeStoragePath": "candidate/cv.pdf",
            "resumeFileName": "cv.pdf",
        }
        mock_extract.side_effect = RuntimeError("extractor failed")
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 500)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    @patch("app.main.fetch_job_for_scoring")
    @patch("app.main.download_resume_for_scoring", return_value=b"resume bytes")
    @patch("app.main.extract_resume_text", return_value=("pdf", "Python, Flutter, Firebase"))
    @patch("app.main.persist_application_score")
    def test_successful_score(
        self,
        mock_persist: Mock,
        _mock_extract: Mock,
        _mock_download: Mock,
        _mock_fetch_job: Mock,
        mock_fetch_application: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch_application.return_value = {
            "applicationId": "app-1",
            "jobId": "job-1",
            "candidateId": "candidate-1",
            "resumeStoragePath": "candidate/cv.pdf",
            "resumeFileName": "cv.pdf",
        }
        _mock_fetch_job.return_value = {
            "title": "Flutter Developer",
            "description": "Build Flutter apps",
            "requiredSkills": "Flutter, Dart, Firebase",
            "requiredExperience": "Minimum 2 years",
            "requiredEducation": "BSCS or BSSE",
        }
        mock_persist.return_value = {
            "applicationId": "app-1",
            "score": 100.0,
            "scoreBreakdown": {
                "skillsScore": 40.0,
                "experienceScore": 25.0,
                "educationScore": 20.0,
                "projectsScore": 15.0,
                "finalScore": 100.0,
                "skillsMax": 40,
                "experienceMax": 25,
                "educationMax": 20,
                "projectsMax": 15,
            },
            "scoringStatus": "scored",
            "scoringModelVersion": 3,
        }
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["score"], 100.0)
        self.assertEqual(response.json()["scoringStatus"], "scored")
        self.assertEqual(
            set(response.json()),
            {
                "applicationId",
                "score",
                "scoreBreakdown",
                "scoringStatus",
                "scoredAt",
                "scoringModelVersion",
            },
        )
        self.mock_persist_scoring_status.assert_called_once_with("app-1", "scoring")
        mock_persist.assert_called_once()
        self.assertEqual(
            mock_persist.call_args.kwargs,
            {"scoring_model_version": 3, "job_id": "job-1"},
        )

    def test_fetch_job_loads_saved_version_two_policy(self) -> None:
        job_data = {
            "title": "Developer",
            "description": "Build software",
            "requiredSkills": "Python",
            "requiredExperience": "2 years",
            "requiredEducation": "BSCS",
            "scoringPolicyVersion": 2,
            "jobType": "experienced",
            "skillsRequirement": "required",
            "experienceRequirement": "required",
            "experienceYears": 2.0,
            "educationRequirement": "preferred",
            "projectsRequirement": "not_applicable",
            "projectCriteria": "",
        }
        snapshot = Mock()
        snapshot.exists = True
        snapshot.to_dict.return_value = job_data
        self.mock_firestore_client.collection.return_value.document.return_value.get.return_value = snapshot

        job = fetch_job_for_scoring("job-1")

        self.assertEqual(job["scoringPolicyVersion"], 2)
        self.assertEqual(job["experienceYears"], 2.0)
        self.assertEqual(job["projectsRequirement"], "not_applicable")
        self.assertEqual(job["requiredSkills"], "Python")
        self.assertEqual(job["requiredEducation"], "BSCS")

    def test_legacy_job_remains_on_legacy_scoring_path(self) -> None:
        snapshot = Mock()
        snapshot.exists = True
        snapshot.to_dict.return_value = {
            "title": "Legacy job",
            "requirements": "Python",
            "requiredExperience": "2 years",
            "requiredEducation": "BSCS",
        }
        self.mock_firestore_client.collection.return_value.document.return_value.get.return_value = snapshot

        job = fetch_job_for_scoring("legacy-job")

        self.assertNotIn("scoringPolicyVersion", job)
        self.assertEqual(normalize_job_scoring_policy(job), {})
        self.assertEqual(job["requiredSkills"], "Python")

    def test_invalid_version_two_policy_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            normalize_job_scoring_policy(
                {
                    "scoringPolicyVersion": 2,
                    "skillsRequirement": "required",
                    "experienceRequirement": "required",
                    "experienceYears": 0,
                    "educationRequirement": "required",
                    "projectsRequirement": "not_applicable",
                    "requiredSkills": "Python",
                    "requiredEducation": "BSCS",
                }
            )

        self.assertEqual(raised.exception.status_code, 400)

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    @patch("app.main.fetch_job_for_scoring")
    @patch("app.main.download_resume_for_scoring", return_value=b"resume bytes")
    @patch("app.main.extract_resume_text", return_value=("pdf", "Python, Flutter, Firebase"))
    @patch("app.main.persist_application_score")
    def test_firestore_success_write(
        self,
        mock_persist: Mock,
        _mock_extract: Mock,
        _mock_download: Mock,
        _mock_fetch_job: Mock,
        mock_fetch_application: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch_application.return_value = {
            "applicationId": "app-1",
            "jobId": "job-1",
            "candidateId": "candidate-1",
            "resumeStoragePath": "candidate/cv.pdf",
            "resumeFileName": "cv.pdf",
        }
        _mock_fetch_job.return_value = {
            "title": "Flutter Developer",
            "description": "Build Flutter apps",
            "requiredSkills": "Flutter, Dart, Firebase",
            "requiredExperience": "Minimum 2 years",
            "requiredEducation": "BSCS or BSSE",
        }
        mock_persist.return_value = {
            "applicationId": "app-1",
            "score": 100.0,
            "scoreBreakdown": {
                "skillsScore": 40.0,
                "experienceScore": 25.0,
                "educationScore": 20.0,
                "projectsScore": 15.0,
                "finalScore": 100.0,
                "skillsMax": 40,
                "experienceMax": 25,
                "educationMax": 20,
                "projectsMax": 15,
            },
            "scoringStatus": "scored",
        }
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 200)
        mock_persist.assert_called_once()
        self.assertEqual(
            mock_persist.call_args.kwargs,
            {"scoring_model_version": 3, "job_id": "job-1"},
        )

    @patch("app.main.verify_firebase_token", return_value="candidate-1")
    @patch("app.main.fetch_application_for_scoring")
    @patch("app.main.fetch_job_for_scoring")
    @patch("app.main.download_resume_for_scoring", return_value=b"resume bytes")
    @patch("app.main.extract_resume_text", side_effect=RuntimeError("bad extraction"))
    @patch("app.main.persist_application_score")
    def test_scoring_failure_preserves_application(
        self,
        mock_persist: Mock,
        _mock_extract: Mock,
        _mock_download: Mock,
        _mock_fetch_job: Mock,
        mock_fetch_application: Mock,
        _mock_verify: Mock,
    ) -> None:
        mock_fetch_application.return_value = {
            "applicationId": "app-1",
            "jobId": "job-1",
            "candidateId": "candidate-1",
            "resumeStoragePath": "candidate/cv.pdf",
            "resumeFileName": "cv.pdf",
        }
        _mock_fetch_job.return_value = {
            "title": "Flutter Developer",
            "description": "Build Flutter apps",
            "requiredSkills": "Flutter, Dart, Firebase",
            "requiredExperience": "Minimum 2 years",
            "requiredEducation": "BSCS or BSSE",
        }
        response = self.client.post(
            "/score-application",
            json={"applicationId": "app-1"},
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 500)
        mock_persist.assert_not_called()
        failure_update = (
            self.mock_firestore_client.collection.return_value
            .document.return_value.update
        )
        failure_update.assert_called_once()
        self.assertEqual(failure_update.call_args.args[0]["scoringStatus"], "failed")
        self.assertEqual(
            failure_update.call_args.args[0]["scoringErrorCode"],
            "EXTRACTION_FAILED",
        )

    def test_score_formula_remains_unchanged(self) -> None:
        result = score_resume(
            ["Flutter", "Dart", "Firebase", "REST API"],
            [{"text": "4 years"}],
            [{"text": "BSSE"}],
            [{"text": "Flutter Dart Firebase REST API"}],
            "Flutter Developer",
            "Flutter, Dart, Firebase, REST API",
            "Minimum 2 years",
            "BSCS or BSSE",
            "Build and maintain Flutter apps.",
        )
        self.assertEqual(result["finalScore"], 100.0)
        self.assertEqual(result["earnedScore"], 100.0)

    def test_success_response_timestamp_is_serializable(self) -> None:
        snapshot = Mock()
        snapshot.exists = True
        snapshot.to_dict.return_value = {}
        self.mock_firestore_client.collection.return_value.document.return_value.get.return_value = snapshot
        transaction = Mock()
        self.mock_firestore_client.transaction.return_value = transaction

        with patch("app.main.admin_firestore.transactional", side_effect=lambda fn: fn):
            payload = persist_application_score(
                "app-1",
                87.5,
                {"finalScore": 87.5},
                scoring_model_version=3,
            )

        self.assertEqual(payload["scoringStatus"], "scored")
        self.assertEqual(payload["scoringModelVersion"], 3)
        self.assertIsInstance(datetime.fromisoformat(payload["scoredAt"]), datetime)
        transaction.set.assert_called_once()

    def test_rescoring_archives_existing_score_without_changing_review_fields(self) -> None:
        old_scored_at = datetime(2026, 11, 5)
        snapshot = Mock()
        snapshot.exists = True
        snapshot.to_dict.return_value = {
            "score": 40.0,
            "scoreBreakdown": {"finalScore": 40.0},
            "scoringModelVersion": None,
            "scoredAt": old_scored_at,
            "reviewStatus": "Pending",
        }
        document = self.mock_firestore_client.collection.return_value.document.return_value
        document.get.return_value = snapshot
        transaction = Mock()
        self.mock_firestore_client.transaction.return_value = transaction

        with patch("app.main.admin_firestore.transactional", side_effect=lambda fn: fn):
            payload = persist_application_score(
                "app-1",
                82.0,
                {"finalScore": 82.0},
                scoring_model_version=3,
            )

        saved = transaction.set.call_args.args[1]
        self.assertEqual(saved["scoringHistory"][0]["score"], 40.0)
        self.assertIsNone(saved["scoringHistory"][0]["scoringModelVersion"])
        self.assertEqual(saved["scoringHistory"][0]["scoredAt"], old_scored_at)
        self.assertEqual(payload["score"], 82.0)
        self.assertNotIn("reviewStatus", saved)

    def test_mixed_version_job_cohort_blocks_score_update(self) -> None:
        snapshot = Mock()
        snapshot.exists = True
        snapshot.to_dict.return_value = {}
        document = self.mock_firestore_client.collection.return_value.document.return_value
        document.get.return_value = snapshot
        other = Mock()
        other.id = "other-application"
        other.to_dict.return_value = {
            "score": 55.0,
            "scoringModelVersion": None,
        }
        self.mock_firestore_client.collection.return_value.where.return_value.stream.return_value = [
            other
        ]
        transaction = Mock()
        self.mock_firestore_client.transaction.return_value = transaction

        with patch("app.main.admin_firestore.transactional", side_effect=lambda fn: fn):
            with self.assertRaises(HTTPException) as raised:
                persist_application_score(
                    "app-1",
                    82.0,
                    {"finalScore": 82.0},
                    scoring_model_version=3,
                    job_id="job-1",
                )

        self.assertEqual(raised.exception.status_code, 409)
        transaction.set.assert_not_called()


class ResumeDownloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment_patcher = patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://project-ref.supabase.co/",
                "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
            },
        )
        self.environment_patcher.start()
        self.addCleanup(self.environment_patcher.stop)

    @patch("app.main.httpx.get")
    def test_download_uses_resumes_bucket_and_object_path_once(
        self,
        mock_get: Mock,
    ) -> None:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"private resume bytes"

        result = download_resume_for_scoring(
            "candidate-1/job-1/application-1/resume file#.pdf"
        )

        self.assertEqual(result, b"private resume bytes")
        request_url = mock_get.call_args.args[0]
        self.assertEqual(
            request_url,
            "https://project-ref.supabase.co/storage/v1/object/resumes/"
            "candidate-1/job-1/application-1/resume%20file%23.pdf",
        )
        self.assertEqual(request_url.count("/storage/v1/object/resumes/"), 1)
        self.assertNotIn("/resumes/resumes/", request_url)
        self.assertEqual(
            mock_get.call_args.kwargs["headers"],
            {
                "Authorization": "Bearer test-service-role-key",
                "apikey": "test-service-role-key",
            },
        )

    @patch("app.main.httpx.get")
    def test_download_rejects_supabase_url_with_api_path(
        self,
        mock_get: Mock,
    ) -> None:
        with patch.dict(
            "os.environ",
            {"SUPABASE_URL": "https://project-ref.supabase.co/rest/v1"},
        ):
            with self.assertRaises(HTTPException) as raised:
                download_resume_for_scoring("candidate-1/resume.pdf")

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(
            raised.exception.detail,
            "Supabase URL must be a project base URL",
        )
        mock_get.assert_not_called()

    @patch("app.main.httpx.get")
    def test_upstream_download_failure_remains_sanitized_502(
        self,
        mock_get: Mock,
    ) -> None:
        mock_get.return_value.status_code = 404
        mock_get.return_value.content = b"upstream details must not escape"

        with self.assertRaises(HTTPException) as raised:
            download_resume_for_scoring("candidate-1/resume.pdf")

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "Resume download failed")
        self.assertNotIn("upstream details", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
