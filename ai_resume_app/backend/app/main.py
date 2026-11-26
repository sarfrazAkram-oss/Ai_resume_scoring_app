import hashlib
import io
import json
import logging
import math
import os
import re
import zipfile
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlsplit

import firebase_admin
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin import firestore as admin_firestore
from google.api_core.exceptions import AlreadyExists
from pydantic import BaseModel

from app.services.resume_extractor import (
    ResumeExtractionError,
    extract_resume_text,
)
from app.services.resume_structurer import extract_structured_information
from app.services.resume_scorer import (
    ExperienceScore,
    SkillsScore,
    score_experience,
    score_skills,
)
from app.services.education_scorer import EducationScore, score_education
from app.services.project_scorer import ProjectsScore, score_projects
from app.services.final_scorer import (
    FinalResumeScore,
    score_resume,
    score_resume_with_policy,
)
from app.services.scoring_v3 import SCORING_MODEL_VERSION, score_resume_v3

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Ranking Backend")

MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024
MAX_MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_UPLOAD_REQUEST_SIZE_BYTES = (
    MAX_RESUME_SIZE_BYTES + MAX_MULTIPART_OVERHEAD_BYTES
)
_SAFE_STORAGE_DOCUMENT_ID = re.compile(r"[A-Za-z0-9_-]+\Z")


def _is_safe_storage_document_id(value: str) -> bool:
    return (
        0 < len(value) <= 1500
        and _SAFE_STORAGE_DOCUMENT_ID.fullmatch(value) is not None
        and not (value.startswith("__") and value.endswith("__"))
    )


class _UploadRequestTooLarge(Exception):
    pass


class UploadRequestSizeLimitMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if (
            scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != "/upload-resume"
        ):
            await self.app(scope, receive, send)
            return

        content_length = next(
            (
                value
                for name, value in scope.get("headers", [])
                if name.lower() == b"content-length"
            ),
            None,
        )
        try:
            declared_size = int(content_length) if content_length is not None else None
        except ValueError:
            declared_size = None
        if (
            declared_size is not None
            and declared_size > MAX_UPLOAD_REQUEST_SIZE_BYTES
        ):
            await self._send_too_large(send)
            return

        received_size = 0
        response_started = False

        async def limited_receive() -> Any:
            nonlocal received_size
            message = await receive()
            if message.get("type") == "http.request":
                received_size += len(message.get("body", b""))
                if received_size > MAX_UPLOAD_REQUEST_SIZE_BYTES:
                    raise _UploadRequestTooLarge
            return message

        async def tracked_send(message: Any) -> None:
            nonlocal response_started
            if message.get("type") == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _UploadRequestTooLarge:
            if not response_started:
                await self._send_too_large(send)

    @staticmethod
    async def _send_too_large(send: Any) -> None:
        body = b'{"detail":"Upload request exceeds the maximum size"}'
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


app.add_middleware(UploadRequestSizeLimitMiddleware)

_DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


def _configured_cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "").strip()
    if not configured:
        return list(_DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_configured_cors_origins(),
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_firebase_admin() -> None:
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip() or os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        "",
    ).strip()
    if service_account_json:
        credentials_obj = credentials.Certificate(json.loads(service_account_json))
    elif service_account_path:
        credentials_obj = credentials.Certificate(service_account_path)
    else:
        credentials_obj = credentials.ApplicationDefault()

    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    options = {"projectId": project_id} if project_id else None
    firebase_admin.initialize_app(credentials_obj, options=options)

def get_firestore_client() -> Any:
    initialize_firebase_admin()
    return admin_firestore.client()


class SkillsScoreRequest(BaseModel):
    resumeSkills: list[str]
    requiredSkills: str | list[str]


class ExperienceScoreRequest(BaseModel):
    resumeExperience: list[dict[str, str]]
    requiredExperience: str


class EducationScoreRequest(BaseModel):
    resumeEducation: list[dict[str, str]]
    requiredEducation: str


class ProjectsScoreRequest(BaseModel):
    resumeProjects: list[dict[str, str]]
    jobTitle: str
    requiredSkills: str | list[str] | None = None
    projectCriteria: str | list[str] | None = None
    jobDescription: str = ""


class FinalResumeScoreRequest(BaseModel):
    resumeSkills: list[str]
    resumeExperience: list[dict[str, str]]
    resumeEducation: list[dict[str, str]]
    resumeProjects: list[dict[str, str]]
    jobTitle: str
    requiredSkills: str | list[str] | None = None
    requiredExperience: str = ""
    requiredEducation: str = ""
    jobDescription: str = ""
    jobPolicy: dict[str, Any] | None = None


class ScoreApplicationRequest(BaseModel):
    applicationId: str
    confirmRescore: bool = False


class ApplicationDuplicateCheckRequest(BaseModel):
    jobId: str


class SubmitApplicationRequest(BaseModel):
    applicationId: str
    jobId: str
    resumeFileName: str
    resumeStoragePath: str
    candidateName: str
    candidateEmail: str


class ApplicationActionRequest(BaseModel):
    applicationId: str

    class Config:
        extra = "forbid"


class ScoreApplicationResponse(BaseModel):
    applicationId: str
    score: float | None
    scoreBreakdown: dict[str, Any] | None
    scoringStatus: str
    scoredAt: str | None = None
    scoringModelVersion: int | None = None


def verify_firebase_token(authorization: str | None) -> str:
    if authorization is None or not authorization.strip():
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization must be Bearer <token>")

    try:
        initialize_firebase_admin()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Firebase authentication is not configured",
        ) from exc

    token = parts[1]
    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception as exc:  # pragma: no cover - real token verification is external
        raise HTTPException(status_code=401, detail="Invalid Firebase token") from exc

    return str(decoded.get("uid") or "")


def candidate_has_application(client: Any, uid: str, job_id: str) -> bool:
    matches = (
        client.collection("applications")
        .where("candidateId", "==", uid)
        .where("jobId", "==", job_id)
        .limit(1)
        .get()
    )
    return bool(matches)


def require_application_candidate_uid(authorization: str | None) -> str:
    uid = verify_firebase_token(authorization)
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    return uid


def require_recruiter_uid(authorization: str | None) -> str:
    uid = verify_firebase_token(authorization)
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    return uid


def _load_recruiter_application_context(
    client: Any,
    transaction: Any,
    application_id: str,
    recruiter_uid: str,
) -> tuple[Any, dict[str, Any], Any, dict[str, Any]]:
    application_reference = (
        client.collection("applications").document(application_id)
    )
    application_snapshot = application_reference.get(transaction=transaction)
    if not application_snapshot.exists:
        raise HTTPException(status_code=404, detail="Application not found")

    application_data = application_snapshot.to_dict() or {}
    if application_data.get("recruiterId") != recruiter_uid:
        raise HTTPException(status_code=403, detail="Application ownership mismatch")
    if application_data.get("applicationId") not in (None, application_id):
        raise HTTPException(status_code=409, detail="Application ID mismatch")

    candidate_id = application_data.get("candidateId")
    job_id = application_data.get("jobId")
    if (
        not isinstance(candidate_id, str)
        or not candidate_id
        or not isinstance(job_id, str)
        or not _is_safe_storage_document_id(job_id)
    ):
        raise HTTPException(
            status_code=409,
            detail="Application candidate or job relationship is invalid",
        )

    job_snapshot = (
        client.collection("jobs").document(job_id).get(transaction=transaction)
    )
    if not job_snapshot.exists:
        raise HTTPException(status_code=404, detail="Job not found")
    job_data = job_snapshot.to_dict() or {}
    if job_data.get("createdBy") != recruiter_uid:
        raise HTTPException(status_code=403, detail="Job ownership mismatch")

    projection_reference = (
        client.collection("candidateApplications").document(application_id)
    )
    projection_snapshot = projection_reference.get(transaction=transaction)
    if not projection_snapshot.exists:
        raise HTTPException(
            status_code=409,
            detail="Candidate application projection not found",
        )
    projection_data = projection_snapshot.to_dict() or {}
    if projection_data.get("applicationId") not in (None, application_id) or any(
        projection_data.get(field) != application_data.get(field)
        for field in ("candidateId", "jobId", "recruiterId")
    ):
        raise HTTPException(
            status_code=409,
            detail="Application and candidate projection do not match",
        )

    return (
        application_reference,
        application_data,
        projection_reference,
        job_data,
    )


def share_existing_application_score(
    application_id: str,
    recruiter_uid: str,
) -> dict[str, Any]:
    if not _is_safe_storage_document_id(application_id):
        raise HTTPException(status_code=400, detail="Invalid application request")

    client = get_firestore_client()

    @admin_firestore.transactional
    def share_score(transaction: Any) -> dict[str, Any]:
        (
            application_reference,
            application_data,
            projection_reference,
            _,
        ) = _load_recruiter_application_context(
            client,
            transaction,
            application_id,
            recruiter_uid,
        )
        score = application_data.get("score")
        score_breakdown = application_data.get("scoreBreakdown")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
            or not isinstance(score_breakdown, dict)
        ):
            raise HTTPException(
                status_code=409,
                detail="A completed score and breakdown are not available",
            )

        transaction.update(application_reference, {"scoreShared": True})
        transaction.update(
            projection_reference,
            {
                "score": score,
                "scoreBreakdown": score_breakdown,
                "scoreShared": True,
            },
        )
        return {
            "success": True,
            "applicationId": application_id,
            "scoreShared": True,
        }

    return share_score(client.transaction())


def reject_application_with_notification(
    application_id: str,
    recruiter_uid: str,
) -> dict[str, Any]:
    if not _is_safe_storage_document_id(application_id):
        raise HTTPException(status_code=400, detail="Invalid application request")

    client = get_firestore_client()
    notification_id = hashlib.sha256(
        f"{application_id}:rejection".encode("utf-8")
    ).hexdigest()
    notification_reference = (
        client.collection("candidateNotifications").document(notification_id)
    )

    @admin_firestore.transactional
    def reject_application(transaction: Any) -> dict[str, Any]:
        (
            application_reference,
            application_data,
            projection_reference,
            job_data,
        ) = _load_recruiter_application_context(
            client,
            transaction,
            application_id,
            recruiter_uid,
        )
        job_title = job_data.get("title")
        if not isinstance(job_title, str) or not job_title.strip():
            raise HTTPException(status_code=409, detail="Job title is unavailable")

        candidate_id = application_data["candidateId"]
        job_id = application_data["jobId"]
        notification_snapshot = notification_reference.get(
            transaction=transaction
        )
        if notification_snapshot.exists:
            existing_notification = notification_snapshot.to_dict() or {}
            if any(
                existing_notification.get(field) != value
                for field, value in {
                    "candidateId": candidate_id,
                    "applicationId": application_id,
                    "jobId": job_id,
                    "type": "rejection",
                }.items()
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Existing rejection notification does not match",
                )

        transaction.update(application_reference, {"status": "Rejected"})
        transaction.update(projection_reference, {"status": "Rejected"})
        if not notification_snapshot.exists:
            transaction.create(
                notification_reference,
                {
                    "candidateId": candidate_id,
                    "applicationId": application_id,
                    "jobId": job_id,
                    "type": "rejection",
                    "title": job_title.strip(),
                    "message": (
                        f"Your application for {job_title.strip()} has been "
                        "reviewed. Unfortunately, you have not been selected "
                        "for this position."
                    ),
                    "createdAt": admin_firestore.SERVER_TIMESTAMP,
                    "read": False,
                },
            )

        return {
            "success": True,
            "applicationId": application_id,
            "status": "Rejected",
            "notificationId": notification_id,
            "notificationSaved": True,
        }

    return reject_application(client.transaction())


def create_candidate_application(
    *,
    application_id: str,
    job_id: str,
    resume_file_name: str,
    resume_storage_path: str,
    candidate_name: str,
    candidate_email: str,
    uid: str,
) -> None:
    if (
        not _is_safe_storage_document_id(application_id)
        or not _is_safe_storage_document_id(job_id)
    ):
        raise HTTPException(status_code=400, detail="Invalid application request")

    extension_parts = resume_file_name.rsplit(".", 1)
    if (
        len(extension_parts) != 2
        or extension_parts[1].lower() not in {"pdf", "docx"}
    ):
        raise HTTPException(status_code=400, detail="Unsupported resume file type")
    expected_resume_storage_path = (
        f"{uid}/{job_id}/{application_id}.{extension_parts[1].lower()}"
    )
    if resume_storage_path != expected_resume_storage_path:
        raise HTTPException(status_code=400, detail="Invalid application request")

    client = get_firestore_client()
    job_document = client.collection("jobs").document(job_id).get()
    if not job_document.exists:
        raise HTTPException(status_code=404, detail="Job not found")
    job_data = job_document.to_dict() or {}
    if job_data.get("status") != "active":
        raise HTTPException(status_code=404, detail="Job not found")
    recruiter_id = job_data.get("createdBy")
    job_title = job_data.get("title")
    company_name = job_data.get("companyName", "")
    if (
        not isinstance(recruiter_id, str)
        or not recruiter_id
        or not isinstance(job_title, str)
        or not job_title
        or not isinstance(company_name, str)
    ):
        raise HTTPException(status_code=400, detail="Job ownership could not be verified")

    if candidate_has_application(client, uid, job_id):
        raise HTTPException(status_code=409, detail="You have already applied to this job.")

    lock_key = json.dumps([uid, job_id], separators=(",", ":"))
    lock_id = hashlib.sha256(lock_key.encode("utf-8")).hexdigest()
    application_reference = client.collection("applications").document(application_id)
    projection_reference = client.collection("candidateApplications").document(
        application_id
    )
    lock_reference = client.collection("applicationSubmissionLocks").document(lock_id)
    application_data = {
        "jobId": job_id,
        "jobTitle": job_title,
        "companyName": company_name,
        "recruiterId": recruiter_id,
        "candidateId": uid,
        "candidateEmail": candidate_email,
        "candidateName": candidate_name,
        "resumeFileName": resume_file_name,
        "resumeStoragePath": resume_storage_path,
        "appliedAt": admin_firestore.SERVER_TIMESTAMP,
        "status": "Pending",
        "score": None,
        "scoringStatus": "pending",
        "scoreShared": False,
    }
    projection_data = {
        "jobId": job_id,
        "jobTitle": job_title,
        "recruiterId": recruiter_id,
        "candidateId": uid,
        "candidateName": candidate_name,
        "resumeFileName": resume_file_name,
        "appliedAt": admin_firestore.SERVER_TIMESTAMP,
        "status": "Pending",
        "scoreShared": False,
    }

    batch = client.batch()
    batch.create(
        lock_reference,
        {
            "applicationId": application_id,
            "jobId": job_id,
            "createdAt": admin_firestore.SERVER_TIMESTAMP,
        },
    )
    batch.create(application_reference, application_data)
    batch.create(projection_reference, projection_data)
    try:
        batch.commit()
    except AlreadyExists as exc:
        raise HTTPException(
            status_code=409,
            detail="An application already exists for this job or request.",
        ) from exc


def fetch_application_for_scoring(application_id: str, uid: str) -> dict[str, Any]:
    application_doc = get_firestore_client().collection("applications").document(application_id).get()
    if not application_doc.exists:
        raise HTTPException(status_code=404, detail="Application not found")

    application_data = application_doc.to_dict() or {}
    application_data["applicationId"] = application_doc.id

    if application_data.get("candidateId") != uid:
        raise HTTPException(status_code=403, detail="Application ownership mismatch")

    return application_data


def normalize_job_scoring_policy(job_data: dict[str, Any]) -> dict[str, Any]:
    policy_version = job_data.get("scoringPolicyVersion")
    if policy_version is None:
        return {}
    try:
        version = int(policy_version)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid scoring policy version") from exc
    if version != 2:
        raise HTTPException(status_code=400, detail="Unsupported scoring policy version")

    state_fields = {
        "skillsRequirement": "skillsRequirement",
        "experienceRequirement": "experienceRequirement",
        "educationRequirement": "educationRequirement",
        "projectsRequirement": "projectsRequirement",
    }
    states: dict[str, str] = {}
    for key, field in state_fields.items():
        value = job_data.get(field)
        if not isinstance(value, str) or value not in {
            "required",
            "preferred",
            "not_applicable",
        }:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or missing scoring applicability: {field}",
            )
        states[key] = value
    if all(value == "not_applicable" for value in states.values()):
        raise HTTPException(
            status_code=400,
            detail="At least one scoring category must be applicable",
        )

    def has_criteria(value: Any) -> bool:
        if isinstance(value, str):
            return bool(re.search(r"[A-Za-z0-9]", value))
        if isinstance(value, list):
            return any(has_criteria(item) for item in value)
        return False

    skills = job_data.get("requiredSkills")
    education = job_data.get("requiredEducation")
    project_criteria = job_data.get("projectCriteria")
    if states["skillsRequirement"] != "not_applicable":
        if not has_criteria(skills) or score_skills([], skills)["skillsScore"] is None:
            raise HTTPException(status_code=400, detail="Applicable skills criteria are missing or invalid")
    if states["educationRequirement"] != "not_applicable":
        if (
            not has_criteria(education)
            or score_education([], str(education))["educationScore"] is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Applicable education criteria are missing or invalid",
            )
    if states["projectsRequirement"] != "not_applicable":
        if (
            not has_criteria(project_criteria)
            or score_projects(
                [],
                str(job_data.get("title") or ""),
                project_criteria,
                str(job_data.get("description") or ""),
            )["projectsScore"]
            is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Applicable project criteria are missing or invalid",
            )

    experience_years: Any = job_data.get("experienceYears")
    if states["experienceRequirement"] != "not_applicable":
        if isinstance(experience_years, bool):
            experience_years = None
        try:
            parsed_years = float(experience_years)
        except (TypeError, ValueError):
            parsed_years = 0.0
        if not math.isfinite(parsed_years) or parsed_years <= 0:
            raise HTTPException(
                status_code=400,
                detail="Applicable experience requires positive experience years",
            )
        experience_years = parsed_years

    return {
        "scoringPolicyVersion": version,
        "jobType": str(job_data.get("jobType") or "").strip(),
        **states,
        "experienceYears": experience_years,
        "projectCriteria": project_criteria,
        "requiredSkills": skills,
        "requiredEducation": education,
    }


def fetch_job_for_scoring(job_id: str) -> dict[str, Any]:
    job_doc = get_firestore_client().collection("jobs").document(job_id).get()
    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = job_doc.to_dict() or {}
    required_skills = job_data.get("requiredSkills")
    if required_skills is None:
        required_skills = job_data.get("requirements")

    legacy = {
        "title": str(job_data.get("title") or ""),
        "description": str(job_data.get("description") or ""),
        "requiredSkills": required_skills,
        "requiredExperience": job_data.get("requiredExperience") or "",
        "requiredEducation": job_data.get("requiredEducation") or "",
        "jobType": str(job_data.get("jobType") or job_data.get("job_type") or ""),
        "projectCriteria": job_data.get("projectCriteria") or job_data.get("project_criteria") or "",
    }
    policy = normalize_job_scoring_policy(job_data)
    if policy:
        legacy.update(policy)
        return legacy
    return legacy


def download_resume_for_scoring(resume_storage_path: str) -> bytes:
    if not resume_storage_path or not resume_storage_path.strip():
        raise HTTPException(status_code=400, detail="Application resumeStoragePath is missing")

    supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase service configuration is missing")
    parsed_url = urlsplit(supabase_url)
    if not parsed_url.scheme or not parsed_url.netloc or parsed_url.path:
        raise HTTPException(status_code=500, detail="Supabase URL must be a project base URL")

    object_path = quote(resume_storage_path.lstrip("/"), safe="/")
    url = f"{supabase_url}/storage/v1/object/resumes/{object_path}"
    try:
        response = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {supabase_key}",
                "apikey": supabase_key,
            },
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        logger.warning("Supabase resume download transport failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Resume download failed") from exc
    if response.status_code >= 400:
        logger.warning("Supabase resume download returned HTTP %s", response.status_code)
        raise HTTPException(status_code=502, detail="Resume download failed")
    return response.content


def persist_application_failure(
    application_id: str,
    error_code: str,
) -> None:
    document = (
        get_firestore_client()
        .collection("applications")
        .document(application_id)
    )
    snapshot = document.get()
    snapshot_data = snapshot.to_dict() if snapshot.exists else {}
    current = snapshot_data if isinstance(snapshot_data, dict) else {}
    if current.get("score") is not None:
        document.update(
            {
                "scoringAttemptStatus": "failed",
                "scoringErrorCode": error_code,
            }
        )
        return
    document.update(
        {
            "scoringStatus": "failed",
            "scoringErrorCode": error_code,
        }
    )


def persist_scoring_status(application_id: str, status: str) -> None:
    document = (
        get_firestore_client()
        .collection("applications")
        .document(application_id)
    )
    snapshot = document.get()
    snapshot_data = snapshot.to_dict() if snapshot.exists else {}
    current = snapshot_data if isinstance(snapshot_data, dict) else {}
    field = (
        "scoringAttemptStatus"
        if current.get("score") is not None
        else "scoringStatus"
    )
    document.update({field: status})


def persist_application_score(
    application_id: str,
    score: float | None,
    score_breakdown: dict[str, Any] | None,
    error_code: str | None = None,
    scoring_model_version: int | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    status = "failed" if score is None else "scored"
    response_scored_at = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "score": score,
        "scoreBreakdown": score_breakdown,
        "scoringStatus": status,
        "scoredAt": admin_firestore.SERVER_TIMESTAMP,
    }
    if scoring_model_version is not None:
        payload["scoringModelVersion"] = scoring_model_version
    if error_code:
        payload["scoringErrorCode"] = error_code

    client = get_firestore_client()
    document = client.collection("applications").document(application_id)
    transaction = client.transaction()

    @admin_firestore.transactional
    def save_score(transaction: Any) -> dict[str, Any]:
        snapshot = document.get(transaction=transaction)
        if not snapshot.exists:
            raise HTTPException(status_code=404, detail="Application not found")
        current = snapshot.to_dict() or {}

        if score is not None and scoring_model_version is not None and job_id:
            cohort = (
                client.collection("applications")
                .where("jobId", "==", job_id)
                .stream(transaction=transaction)
            )
            for other_application in cohort:
                if other_application.id == application_id:
                    continue
                other = other_application.to_dict() or {}
                if other.get("score") is None:
                    continue
                other_version = other.get("scoringModelVersion")
                if other_version is None:
                    other_breakdown = other.get("scoreBreakdown")
                    if isinstance(other_breakdown, dict):
                        other_version = other_breakdown.get("scoringModelVersion")
                if other_version != scoring_model_version:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "This job has scored applications using another scoring "
                            "model version. Rescore the full cohort before updating "
                            "this application."
                        ),
                    )

        history = list(current.get("scoringHistory") or [])
        if current.get("score") is not None:
            history.append(
                {
                    "score": current.get("score"),
                    "scoreBreakdown": current.get("scoreBreakdown"),
                    "scoringModelVersion": current.get("scoringModelVersion"),
                    "scoredAt": current.get("scoredAt"),
                }
            )
        score_payload = {
            **payload,
            "scoringHistory": history,
            "scoringErrorCode": admin_firestore.DELETE_FIELD,
            "scoringAttemptStatus": admin_firestore.DELETE_FIELD,
        }
        transaction.set(document, score_payload, merge=True)
        return {
            "applicationId": application_id,
            "score": score,
            "scoreBreakdown": score_breakdown,
            "scoringStatus": status,
            "scoredAt": response_scored_at,
            "scoringModelVersion": scoring_model_version,
        }

    return save_score(transaction)


def score_application_for_application(
    application_id: str,
    uid: str,
    *,
    confirm_rescore: bool = False,
) -> dict[str, Any]:
    application = fetch_application_for_scoring(application_id, uid)
    if application.get("score") is not None and not confirm_rescore:
        raise HTTPException(
            status_code=409,
            detail="Rescoring an existing application requires explicit confirmation.",
        )
    persist_scoring_status(application_id, "scoring")
    try:
        job_id = application.get("jobId")
        if not job_id:
            raise HTTPException(status_code=400, detail="Application jobId is missing")

        job = fetch_job_for_scoring(str(job_id))
        resume_storage_path = str(application.get("resumeStoragePath") or "").strip()
        if not resume_storage_path:
            raise HTTPException(
                status_code=400,
                detail="Application resumeStoragePath is missing",
            )

        try:
            resume_bytes = download_resume_for_scoring(resume_storage_path)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Resume download failed",
            ) from exc
        resume_file_name = str(
            application.get("resumeFileName") or resume_storage_path.rsplit("/", 1)[-1]
        )

        try:
            _, text = extract_resume_text(resume_file_name, resume_bytes)
        except ResumeExtractionError:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Resume extraction failed",
            ) from exc
        structured = extract_structured_information(text)
        policy = normalize_job_scoring_policy(job)
        result = score_resume_v3(
            list(structured.get("skills", [])),
            list(structured.get("employmentEvidence", [])),
            list(structured.get("education", [])),
            text,
            str(job.get("title") or ""),
            job.get("requiredSkills") or "",
            str(job.get("requiredExperience") or ""),
            str(job.get("requiredEducation") or ""),
            str(job.get("description") or ""),
            job_policy=policy or None,
        )
        score_breakdown = {
            "scoringModelVersion": result["scoringModelVersion"],
            "jobScoringPolicyVersion": result["jobScoringPolicyVersion"],
            "skillsScore": result["components"]["skills"]["score"],
            "skillsMax": result["components"]["skills"]["maxScore"],
            "experienceScore": result["components"]["experience"]["score"],
            "experienceMax": result["components"]["experience"]["maxScore"],
            "educationScore": result["components"]["education"]["score"],
            "educationMax": result["components"]["education"]["maxScore"],
            "practicalWorkScore": result["components"]["practicalWork"]["score"],
            "practicalWorkMax": result["components"]["practicalWork"]["maxScore"],
            "projectsScore": result["components"]["practicalWork"]["score"],
            "projectsMax": result["components"]["practicalWork"]["maxScore"],
            "finalScore": result["score"],
            "components": result["components"],
        }
        return persist_application_score(
            application_id,
            float(result["score"]),
            score_breakdown,
            scoring_model_version=SCORING_MODEL_VERSION,
            job_id=str(job_id),
        )
    except HTTPException as exc:
        error_code = {
            400: "INVALID_SCORING_INPUT",
            404: "SCORING_SOURCE_NOT_FOUND",
            500: "SCORING_FAILED",
            502: "RESUME_DOWNLOAD_FAILED",
        }.get(exc.status_code, "SCORING_FAILED")
        if exc.status_code == 500 and exc.detail == "Resume extraction failed":
            error_code = "EXTRACTION_FAILED"
        elif exc.status_code == 400 and "not scorable" in str(exc.detail).lower():
            error_code = "NO_SCORABLE_REQUIREMENTS"
        persist_application_failure(application_id, error_code)
        raise
    except ResumeExtractionError as exc:
        persist_application_failure(application_id, "EXTRACTION_FAILED")
        raise HTTPException(status_code=500, detail="Resume extraction failed") from exc
    except Exception as exc:
        persist_application_failure(application_id, "SCORING_FAILED")
        raise HTTPException(status_code=500, detail="Resume scoring failed") from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract-resume")
async def extract_resume(file: UploadFile = File(...)) -> dict[str, str | int]:
    file_name = file.filename or ""
    file_bytes = await file.read()
    try:
        file_type, text = extract_resume_text(file_name, file_bytes)
    except ResumeExtractionError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error),
        ) from error

    return {
        "fileName": file_name,
        "fileType": file_type,
        "text": text,
        "characterCount": len(text),
    }


@app.post("/extract-resume-structured")
async def extract_resume_structured(
    file: UploadFile = File(...),
) -> dict[str, Any]:
    file_name = file.filename or ""
    file_bytes = await file.read()
    try:
        file_type, text = extract_resume_text(file_name, file_bytes)
    except ResumeExtractionError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error),
        ) from error

    return {
        "fileName": file_name,
        "fileType": file_type,
        "characterCount": len(text),
        "structured": extract_structured_information(text),
    }


@app.post("/score-skills", response_model=SkillsScore)
def score_resume_skills(request: SkillsScoreRequest) -> SkillsScore:
    return score_skills(request.resumeSkills, request.requiredSkills)


@app.post("/score-experience", response_model=ExperienceScore)
def score_resume_experience(request: ExperienceScoreRequest) -> ExperienceScore:
    return score_experience(request.resumeExperience, request.requiredExperience)


@app.post("/score-education", response_model=EducationScore)
def score_resume_education(request: EducationScoreRequest) -> EducationScore:
    return score_education(request.resumeEducation, request.requiredEducation)


@app.post("/score-projects", response_model=ProjectsScore)
def score_resume_projects(request: ProjectsScoreRequest) -> ProjectsScore:
    return score_projects(
        request.resumeProjects,
        request.jobTitle,
        request.projectCriteria or request.requiredSkills,
        request.jobDescription,
    )


@app.post("/score-resume", response_model=FinalResumeScore)
def score_complete_resume(request: FinalResumeScoreRequest) -> FinalResumeScore:
    if request.jobPolicy:
        return score_resume_with_policy(
            request.resumeSkills,
            request.resumeExperience,
            request.resumeEducation,
            request.resumeProjects,
            request.jobTitle,
            request.requiredSkills,
            request.requiredExperience,
            request.requiredEducation,
            request.jobDescription,
            job_policy=request.jobPolicy,
        )
    return score_resume(
        request.resumeSkills,
        request.resumeExperience,
        request.resumeEducation,
        request.resumeProjects,
        request.jobTitle,
        request.requiredSkills,
        request.requiredExperience,
        request.requiredEducation,
        request.jobDescription,
    )


@app.post("/score-application")
def score_application_endpoint(
    request: ScoreApplicationRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ScoreApplicationResponse:
    uid = verify_firebase_token(authorization)
    payload = score_application_for_application(
        request.applicationId,
        uid,
        confirm_rescore=request.confirmRescore,
    )
    return ScoreApplicationResponse(**payload)


@app.post("/share-application-score")
def share_application_score_endpoint(
    request: ApplicationActionRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, Any]:
    recruiter_uid = require_recruiter_uid(authorization)
    return share_existing_application_score(request.applicationId, recruiter_uid)


@app.post("/reject-application")
def reject_application_endpoint(
    request: ApplicationActionRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, Any]:
    recruiter_uid = require_recruiter_uid(authorization)
    return reject_application_with_notification(request.applicationId, recruiter_uid)


@app.post("/application-duplicate-check")
def application_duplicate_check_endpoint(
    request: ApplicationDuplicateCheckRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, bool]:
    uid = require_application_candidate_uid(authorization)
    if not request.jobId:
        raise HTTPException(status_code=400, detail="Job ID is required")
    client = get_firestore_client()
    return {
        "duplicate": candidate_has_application(client, uid, request.jobId),
    }


@app.post("/upload-resume")
async def upload_resume_endpoint(
    file: UploadFile = File(...),
    application_id: str = Form(..., alias="applicationId"),
    job_id: str = Form(..., alias="jobId"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, str]:
    uid = require_application_candidate_uid(authorization)
    if (
        not _is_safe_storage_document_id(application_id)
        or not _is_safe_storage_document_id(job_id)
    ):
        raise HTTPException(status_code=400, detail="Invalid application request")

    client = get_firestore_client()
    job_document = client.collection("jobs").document(job_id).get()
    if not job_document.exists:
        raise HTTPException(status_code=404, detail="Job not found")
    job_data = job_document.to_dict() or {}
    if job_data.get("status") != "active":
        raise HTTPException(status_code=404, detail="Job not found")
    if candidate_has_application(client, uid, job_id):
        raise HTTPException(
            status_code=409,
            detail="You have already applied to this job.",
        )

    file_name = file.filename or ""
    extension_parts = file_name.rsplit(".", 1)
    if len(extension_parts) != 2:
        raise HTTPException(status_code=400, detail="Unsupported resume file type")
    extension = extension_parts[1].lower()
    content_types = {
        "pdf": "application/pdf",
        "docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    }
    expected_content_type = content_types.get(extension)
    actual_content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if expected_content_type is None or actual_content_type not in {
        expected_content_type,
        "application/octet-stream",
    }:
        raise HTTPException(status_code=400, detail="Unsupported resume file type")

    first_byte = await file.read(1)
    if not first_byte:
        raise HTTPException(status_code=400, detail="Resume file is empty")
    file_bytes = first_byte + await file.read(MAX_RESUME_SIZE_BYTES)
    if len(file_bytes) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Resume file exceeds the 10 MiB limit",
        )

    if extension == "pdf":
        if b"%PDF-" not in file_bytes[:1024]:
            raise HTTPException(status_code=400, detail="Invalid resume file content")
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                document_parts = set(archive.namelist())
        except (OSError, zipfile.BadZipFile) as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid resume file content",
            ) from exc
        if not {"[Content_Types].xml", "word/document.xml"}.issubset(
            document_parts
        ):
            raise HTTPException(status_code=400, detail="Invalid resume file content")

    resume_storage_path = f"{uid}/{job_id}/{application_id}.{extension}"
    supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase service configuration is missing",
        )
    parsed_url = urlsplit(supabase_url)
    if not parsed_url.scheme or not parsed_url.netloc or parsed_url.path:
        raise HTTPException(
            status_code=500,
            detail="Supabase URL must be a project base URL",
        )

    object_path = quote(resume_storage_path, safe="/")
    url = f"{supabase_url}/storage/v1/object/resumes/{object_path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as storage_client:
            response = await storage_client.post(
                url,
                content=file_bytes,
                headers={
                    "Authorization": f"Bearer {supabase_key}",
                    "apikey": supabase_key,
                    "Content-Type": expected_content_type,
                    "x-upsert": "false",
                },
            )
    except httpx.HTTPError as exc:
        logger.warning(
            "Supabase resume upload transport failed (%s)",
            type(exc).__name__,
        )
        raise HTTPException(status_code=502, detail="Resume upload failed") from exc
    if response.status_code >= 400:
        logger.warning("Supabase resume upload returned HTTP %s", response.status_code)
        raise HTTPException(status_code=502, detail="Resume upload failed")

    return {"resumeStoragePath": resume_storage_path}


@app.post("/submit-application")
def submit_application_endpoint(
    request: SubmitApplicationRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, str]:
    uid = require_application_candidate_uid(authorization)
    create_candidate_application(
        application_id=request.applicationId,
        job_id=request.jobId,
        resume_file_name=request.resumeFileName,
        resume_storage_path=request.resumeStoragePath,
        candidate_name=request.candidateName,
        candidate_email=request.candidateEmail,
        uid=uid,
    )
    return {"applicationId": request.applicationId}