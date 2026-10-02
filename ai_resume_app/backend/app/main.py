import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlsplit

import firebase_admin
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin import firestore as admin_firestore
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
from app.services.final_scorer import FinalResumeScore, score_resume

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Ranking Backend")

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
    jobDescription: str


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


class ScoreApplicationRequest(BaseModel):
    applicationId: str


class ScoreApplicationResponse(BaseModel):
    applicationId: str
    score: float | None
    scoreBreakdown: dict[str, Any] | None
    scoringStatus: str
    scoredAt: str | None = None


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


def fetch_application_for_scoring(application_id: str, uid: str) -> dict[str, Any]:
    application_doc = get_firestore_client().collection("applications").document(application_id).get()
    if not application_doc.exists:
        raise HTTPException(status_code=404, detail="Application not found")

    application_data = application_doc.to_dict() or {}
    application_data["applicationId"] = application_doc.id

    if application_data.get("candidateId") != uid:
        raise HTTPException(status_code=403, detail="Application ownership mismatch")

    return application_data


def fetch_job_for_scoring(job_id: str) -> dict[str, Any]:
    job_doc = get_firestore_client().collection("jobs").document(job_id).get()
    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = job_doc.to_dict() or {}
    required_skills = job_data.get("requiredSkills")
    if required_skills is None:
        required_skills = job_data.get("requirements")

    return {
        "title": str(job_data.get("title") or ""),
        "description": str(job_data.get("description") or ""),
        "requiredSkills": required_skills,
        "requiredExperience": job_data.get("requiredExperience") or "",
        "requiredEducation": job_data.get("requiredEducation") or "",
    }


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
    get_firestore_client().collection("applications").document(application_id).update({
        "scoringStatus": "failed",
        "scoringErrorCode": error_code,
        "scoredAt": admin_firestore.SERVER_TIMESTAMP,
    })


def persist_scoring_status(application_id: str, status: str) -> None:
    get_firestore_client().collection("applications").document(application_id).update({
        "scoringStatus": status,
        "scoredAt": admin_firestore.SERVER_TIMESTAMP,
    })


def _build_score_breakdown(result: FinalResumeScore) -> dict[str, Any]:
    skills = result["skills"]
    experience = result["experience"]
    education = result["education"]
    projects = result["projects"]

    return {
        "skillsScore": skills.get("skillsScore"),
        "experienceScore": experience.get("experienceScore"),
        "educationScore": education.get("educationScore"),
        "projectsScore": projects.get("projectsScore"),
        "finalScore": result["finalScore"],
        "skillsMax": int(skills["maxScore"]),
        "experienceMax": int(experience["maxScore"]),
        "educationMax": int(education["maxScore"]),
        "projectsMax": int(projects["maxScore"]),
    }


def persist_application_score(
    application_id: str,
    score: float | None,
    score_breakdown: dict[str, Any] | None,
    error_code: str | None = None,
) -> dict[str, Any]:
    status = "failed" if score is None else "scored"
    response_scored_at = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "score": score,
        "scoreBreakdown": score_breakdown,
        "scoringStatus": status,
        "scoredAt": admin_firestore.SERVER_TIMESTAMP,
    }
    if error_code:
        payload["scoringErrorCode"] = error_code
    get_firestore_client().collection("applications").document(application_id).update(payload)
    return {
        "applicationId": application_id,
        "score": score,
        "scoreBreakdown": score_breakdown,
        "scoringStatus": status,
        "scoredAt": response_scored_at,
    }


def score_application_for_application(application_id: str, uid: str) -> dict[str, Any]:
    application = fetch_application_for_scoring(application_id, uid)
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
        result = score_resume(
            list(structured.get("skills", [])),
            list(structured.get("experience", [])),
            list(structured.get("education", [])),
            list(structured.get("projects", [])),
            str(job.get("title") or ""),
            job.get("requiredSkills") or "",
            str(job.get("requiredExperience") or ""),
            str(job.get("requiredEducation") or ""),
            str(job.get("description") or ""),
        )

        if result["finalScore"] is None:
            raise HTTPException(
                status_code=400,
                detail="The job requirements are not scorable for this resume.",
            )

        score_breakdown = _build_score_breakdown(result)
        return persist_application_score(
            application_id,
            float(result["finalScore"]),
            score_breakdown,
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
) -> dict[str, str | int | dict[str, list[str] | list[dict[str, str]]]]:
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
        request.requiredSkills,
        request.jobDescription,
    )


@app.post("/score-resume", response_model=FinalResumeScore)
def score_complete_resume(request: FinalResumeScoreRequest) -> FinalResumeScore:
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
    payload = score_application_for_application(request.applicationId, uid)
    return ScoreApplicationResponse(**payload)