"""Audit or repair one candidate-safe application projection.

The command is read-only by default. Use --apply only after reviewing the
audit output and separately approving the repair write.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import firestore
from google.api_core.exceptions import AlreadyExists

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(dotenv_path=BACKEND_DIR / ".env", override=False)

service_account_path = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    "",
).strip()
if service_account_path:
    configured_path = Path(service_account_path).expanduser()
    if not configured_path.is_absolute():
        configured_path = BACKEND_DIR / configured_path
    os.environ["FIREBASE_SERVICE_ACCOUNT_PATH"] = str(
        configured_path.resolve()
    )

google_credentials_path = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "",
).strip()
if google_credentials_path:
    configured_path = Path(google_credentials_path).expanduser()
    if not configured_path.is_absolute():
        configured_path = BACKEND_DIR / configured_path
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        configured_path.resolve()
    )

from app.main import initialize_firebase_admin


PROJECTION_FIELDS = (
    "jobId",
    "jobTitle",
    "recruiterId",
    "candidateId",
    "candidateName",
    "resumeFileName",
    "appliedAt",
    "status",
    "scoreShared",
)


REQUIRED_STRING_FIELDS = (
    "jobId",
    "jobTitle",
    "recruiterId",
    "candidateId",
    "candidateName",
    "resumeFileName",
)
PERMITTED_PROJECT_ID = "ai-resume-ranking-system"


def verify_environment_project() -> None:
    configured_project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    if configured_project_id != PERMITTED_PROJECT_ID:
        raise RuntimeError("firebase-project-id-missing-or-mismatched")


def verify_permitted_project() -> None:
    try:
        app = firebase_admin.get_app()
    except ValueError:
        raise RuntimeError("firebase-app-not-initialized")

    project_id = getattr(app, "project_id", None)
    if not isinstance(project_id, str) or not project_id.strip():
        project_id = None
        options = getattr(app, "options", None)
        if isinstance(options, dict):
            option_project_id = options.get("projectId")
            if isinstance(option_project_id, str) and option_project_id.strip():
                project_id = option_project_id.strip()

    if project_id is None:
        raise RuntimeError("firebase-project-id-missing")
    if project_id != PERMITTED_PROJECT_ID:
        raise RuntimeError("firebase-project-id-mismatch")

    try:
        credential_project_id = app.credential.project_id
    except Exception:
        raise RuntimeError("firebase-credential-project-unconfirmed")

    if not isinstance(credential_project_id, str):
        raise RuntimeError("firebase-credential-project-unconfirmed")

    credential_project_id = credential_project_id.strip()
    if not credential_project_id:
        raise RuntimeError("firebase-credential-project-unconfirmed")
    if credential_project_id != PERMITTED_PROJECT_ID:
        raise RuntimeError("firebase-credential-project-mismatch")


def validate_application(
    application_id: str,
    candidate_id: str,
    application: dict[str, Any],
) -> dict[str, Any]:
    missing_or_invalid: list[str] = []

    for field_name in REQUIRED_STRING_FIELDS:
        value = application.get(field_name)
        if not isinstance(value, str) or not value.strip():
            missing_or_invalid.append(field_name)

    if "appliedAt" not in application or application["appliedAt"] is None:
        missing_or_invalid.append("appliedAt")

    status = application.get("status")
    if not isinstance(status, str) or not status.strip():
        missing_or_invalid.append("status")

    if not isinstance(application.get("scoreShared"), bool):
        missing_or_invalid.append("scoreShared")

    if application.get("candidateId") != candidate_id:
        missing_or_invalid.append("candidateId (does not match --candidate-id)")

    if missing_or_invalid:
        raise ValueError("application-validation-failed")

    return {
        "jobId": application["jobId"],
        "jobTitle": application["jobTitle"],
        "recruiterId": application["recruiterId"],
        "candidateId": application["candidateId"],
        "candidateName": application["candidateName"],
        "resumeFileName": application["resumeFileName"],
        "appliedAt": application["appliedAt"],
        "status": application["status"],
        "scoreShared": application["scoreShared"],
    }


def repair_application(
    *,
    application_id: str,
    candidate_id: str,
    apply: bool,
) -> dict[str, Any]:
    try:
        verify_environment_project()
    except RuntimeError as error:
        category = (
            str(error)
            if str(error) == "firebase-project-id-missing-or-mismatched"
            else "firebase-project-verification-failed"
        )
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "stopped",
            "errorCategory": category,
            "reason": "The Firebase project could not be verified safely.",
        }

    try:
        initialize_firebase_admin()
    except Exception:
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "stopped",
            "errorCategory": "firebase-initialization-failed",
            "reason": "Firebase Admin could not be initialized safely.",
        }

    try:
        verify_permitted_project()
    except RuntimeError as error:
        category = {
            "firebase-app-not-initialized": "firebase-app-not-initialized",
            "firebase-project-id-missing": "firebase-project-id-missing",
            "firebase-project-id-mismatch": "firebase-project-id-mismatch",
            "firebase-credential-project-unconfirmed":
                "firebase-credential-project-unconfirmed",
            "firebase-credential-project-mismatch":
                "firebase-credential-project-mismatch",
        }.get(
            error.args[0] if error.args else "",
            "firebase-project-verification-failed",
        )
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "stopped",
            "errorCategory": category,
            "reason": "The active Firebase project does not match the permitted project.",
        }

    try:
        client = firestore.client()
        application_document = (
            client.collection("applications").document(application_id).get()
        )
    except Exception:
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "stopped",
            "errorCategory": "firestore-read-failed",
            "reason": "The private application could not be read safely.",
        }
    if not application_document.exists:
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "stopped",
            "reason": "Private application document was not found.",
        }

    application = application_document.to_dict() or {}
    projection_reference = (
        client.collection("candidateApplications").document(application_id)
    )
    try:
        projection_document = projection_reference.get()
    except Exception:
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "stopped",
            "errorCategory": "firestore-read-failed",
            "reason": "The candidate projection could not be checked safely.",
        }
    if projection_document.exists:
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "skipped",
            "reason": "Candidate projection already exists; it was not overwritten.",
        }

    try:
        projection = validate_application(application_id, candidate_id, application)
    except ValueError:
        return {
            "mode": "apply" if apply else "audit",
            "applicationId": application_id,
            "result": "stopped",
            "errorCategory": "application-validation-failed",
            "reason": "Required application fields are missing or inconsistent.",
        }

    audit_result = {
        "mode": "apply" if apply else "audit",
        "applicationId": application_id,
        "projectionExists": False,
        "result": "eligible" if not apply else "not-written",
        "projectionFields": list(PROJECTION_FIELDS),
    }
    if not apply:
        return audit_result

    try:
        projection_reference.create(projection)
    except AlreadyExists:
        return {
            "mode": "apply",
            "applicationId": application_id,
            "result": "skipped",
            "reason": "Projection was created concurrently; it was not overwritten.",
        }
    except Exception:
        return {
            "mode": "apply",
            "applicationId": application_id,
            "result": "failed",
            "errorCategory": "firestore-write-failed",
            "reason": "The projection could not be created safely.",
        }

    return {
        "mode": "apply",
        "applicationId": application_id,
        "projectionExists": False,
        "result": "created",
        "projectionFields": list(PROJECTION_FIELDS),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--application-id",
        required=True,
        help="Exact private application document ID.",
    )
    parser.add_argument(
        "--candidate-id",
        required=True,
        help="Expected authenticated Firebase candidate UID.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the one missing projection. Omit for a read-only audit.",
    )
    args = parser.parse_args()
    if not args.application_id.strip():
        parser.error("--application-id must not be empty")
    if not args.candidate_id.strip():
        parser.error("--candidate-id must not be empty")

    try:
        result = repair_application(
            application_id=args.application_id.strip(),
            candidate_id=args.candidate_id.strip(),
            apply=args.apply,
        )
    except Exception:
        result = {
            "mode": "apply" if args.apply else "audit",
            "applicationId": args.application_id.strip(),
            "result": "stopped",
            "errorCategory": "repair-operation-failed",
            "reason": "The repair operation stopped safely.",
        }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
