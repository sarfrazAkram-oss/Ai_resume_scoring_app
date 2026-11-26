"""Reproduce synthetic matcher checks and inventory the existing resume sample."""

from __future__ import annotations

import csv
import json
import sys
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.services.resume_scorer as resume_scorer
from app.services.job_relevance_scorer import score_job_relevance
from app.services.resume_extractor import extract_resume_text
from app.services.resume_structurer import extract_structured_information

EVALUATION_AS_OF = date(2026, 11, 4)


class _EvaluationDate(date):
    @classmethod
    def today(cls) -> _EvaluationDate:
        return cls(
            EVALUATION_AS_OF.year,
            EVALUATION_AS_OF.month,
            EVALUATION_AS_OF.day,
        )


def _evaluate_synthetic_cases() -> list[dict[str, Any]]:
    case_path = ROOT / "data" / "job_relevance_eval_cases.json"
    payload = json.loads(case_path.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []

    for case in payload["cases"]:
        result = score_job_relevance(
            case["jobTitle"],
            case["jobDescription"],
            case["requiredSkills"],
            case.get("experienceRequirement"),
            case["employmentEvidence"],
        )
        predicted = (
            result["roles"][0]["relevanceStatus"]
            if len(result["roles"]) == 1
            else (
                "direct"
                if any(role["relevanceStatus"] == "direct" for role in result["roles"])
                else (
                    "transferable"
                    if any(
                        role["relevanceStatus"] == "transferable"
                        for role in result["roles"]
                    )
                    else (
                        "unrelated"
                        if all(
                            role["relevanceStatus"] == "unrelated"
                            for role in result["roles"]
                        )
                        else "insufficient_evidence"
                    )
                )
            )
        )
        review_needed = bool(result["reviewNeededDurations"]) or any(
            role["relevanceStatus"] == "insufficient_evidence"
            for role in result["roles"]
        )
        expected_review = case.get("expectedReviewNeeded")
        expected_direct_months = case.get("expectedTotalDirectRelevantMonths")
        expected_transferable_months = case.get("expectedTotalTransferableMonths")
        checks: dict[str, bool] = {
            "provisionalLabelAgreement": predicted == case["expectedLabel"],
        }
        if expected_review is not None:
            checks["reviewStatus"] = review_needed == expected_review
        if expected_direct_months is not None:
            checks["directDuration"] = (
                result["totalDirectRelevantMonths"] == expected_direct_months
            )
        if expected_transferable_months is not None:
            checks["transferableDuration"] = (
                result["totalTransferableMonths"] == expected_transferable_months
            )
        if case.get("expectedDateStatus"):
            checks["dateStatus"] = all(
                role["dateVerificationStatus"] == case["expectedDateStatus"]
                for role in result["roles"]
            )
        results.append(
            {
                "caseId": case["caseId"],
                "domain": case["domain"],
                "purpose": case["purpose"],
                "expectedLabel": case["expectedLabel"],
                "predictedLabel": predicted,
                "provisionalLabelAgreement": checks["provisionalLabelAgreement"],
                "checks": checks,
                "reviewNeeded": review_needed,
                "totalDirectRelevantMonths": result["totalDirectRelevantMonths"],
                "totalTransferableMonths": result["totalTransferableMonths"],
                "roles": [
                    {
                        "relevanceStatus": role["relevanceStatus"],
                        "dateVerificationStatus": role["dateVerificationStatus"],
                        "durationVerificationStatus": role[
                            "durationVerificationStatus"
                        ],
                        "matchedJobRequirements": role["matchedJobRequirements"],
                        "matchedResponsibilities": role[
                            "matchedResponsibilities"
                        ],
                        "matchedRoleTechnologies": role[
                            "matchedRoleTechnologies"
                        ],
                        "supportingEvidenceSnippets": role[
                            "supportingEvidenceSnippets"
                        ],
                        "relevanceExplanation": role["relevanceExplanation"],
                    }
                    for role in result["roles"]
                ],
            }
        )
    return results


def _inventory_existing_resume_sample() -> dict[str, Any]:
    candidates_path = ROOT / "data" / "ranking_eval" / "candidates.csv"
    archive_path = ROOT / "data" / "raw" / "archive (2).zip"
    with candidates_path.open(encoding="utf-8-sig", newline="") as stream:
        candidates = list(csv.DictReader(stream))

    counts: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    with zipfile.ZipFile(archive_path) as archive:
        for candidate in candidates:
            categories[candidate["category"]] += 1
            with archive.open(candidate["archive_member"]) as pdf_stream:
                file_bytes = pdf_stream.read()
            _, text = extract_resume_text(
                candidate["archive_member"],
                file_bytes,
            )
            structured = extract_structured_information(text)
            evidence = structured.get("employmentEvidence", [])
            counts["parsedResumeFiles"] += 1
            counts["extractedEmploymentRecords"] += len(evidence)
            counts["resumesWithEmploymentRecords"] += bool(evidence)
            counts["recordsWithTitle"] += sum(
                bool(role.get("title")) for role in evidence
            )
            counts["recordsWithResponsibilities"] += sum(
                bool(role.get("responsibilities")) for role in evidence
            )
            counts["recordsWithVerifiedDates"] += sum(
                role.get("dateEvidence", {}).get("status") == "verified"
                for role in evidence
            )
            counts["recordsWithMissingDates"] += sum(
                role.get("dateEvidence", {}).get("status") == "missing_dates"
                for role in evidence
            )
            counts["recordsWithAmbiguousDates"] += sum(
                role.get("dateEvidence", {}).get("status") == "ambiguous_dates"
                for role in evidence
            )
            counts["recordsWithAmbiguousExtraction"] += sum(
                role.get("extractionConfidence") != "high" for role in evidence
            )

    return {
        "source": "existing archive (2).zip candidate sample",
        "sampleSize": len(candidates),
        "categoryCountsUsedForStratificationOnly": dict(sorted(categories.items())),
        "provenanceIndependentlyVerified": False,
        "authenticJobPairingsAvailable": False,
        "independentHumanRelevanceLabelsAvailable": False,
        "employmentEvidenceInventory": dict(counts),
        "interpretation": (
            "Resume files were locally parsed for evidence availability only. "
            "No job-fit labels are inferred from archive categories."
        ),
    }


def evaluate() -> dict[str, Any]:
    with patch.object(resume_scorer, "date", _EvaluationDate):
        cases = _evaluate_synthetic_cases()
        checks = [
            outcome
            for case in cases
            for check_name, outcome in case["checks"].items()
            if check_name != "provisionalLabelAgreement"
        ]
        domain_summary: dict[str, Any] = {}
        for domain in sorted({case["domain"] for case in cases}):
            domain_cases = [case for case in cases if case["domain"] == domain]
            domain_summary[domain] = {
                "caseCount": len(domain_cases),
                "provisionalAgreements": sum(
                    case["provisionalLabelAgreement"] for case in domain_cases
                ),
                "provisionalDisagreements": sum(
                    not case["provisionalLabelAgreement"] for case in domain_cases
                ),
                "predictedLabels": dict(
                    Counter(case["predictedLabel"] for case in domain_cases)
                ),
            }
        return {
            "matcherVersion": 1,
            "evaluationAsOf": EVALUATION_AS_OF.isoformat(),
            "evaluationKind": "offline_only",
            "syntheticCases": cases,
            "syntheticCaseCount": len(cases),
            "syntheticDomainSummary": domain_summary,
            "provisionalEngineeringAgreements": sum(
                case["provisionalLabelAgreement"] for case in cases
            ),
            "provisionalEngineeringDisagreements": sum(
                not case["provisionalLabelAgreement"] for case in cases
            ),
            "durationAndReviewChecks": {
                "passed": sum(checks),
                "total": len(checks),
            },
            "archiveResumeInventory": _inventory_existing_resume_sample(),
            "realResumeJobPairEvaluations": 0,
            "accuracyMetricsProduced": False,
        }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
