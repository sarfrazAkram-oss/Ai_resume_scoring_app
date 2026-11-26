"""Inactive, deterministic job-relevance analysis for employment evidence."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from app.services.resume_scorer import _dated_range_months


RELEVANCE_MATCHER_VERSION = 1

_DOMAIN_EVIDENCE: dict[str, dict[str, tuple[str, ...]]] = {
    "software_it": {
        "titles": (
            "software engineer", "software developer", "flutter developer",
            "web developer", "mobile developer", "programmer", "it specialist",
        ),
        "responsibilities": (
            "develop software", "build applications", "develop applications",
            "maintain code", "debug software", "design apis", "deploy applications",
            "mobile app development", "software development", "application development",
        ),
        "tools": (
            "flutter", "python", "java", "javascript", "typescript", "react",
            "sql", "fastapi", "docker", "kubernetes", "aws", "azure",
        ),
    },
    "healthcare": {
        "titles": (
            "nurse", "nursing", "registered nurse", "nursing assistant", "care assistant",
        ),
        "responsibilities": (
            "patient care", "administer medication", "assess patients",
            "monitor patient", "clinical care", "nursing care", "patient records",
            "care plans",
        ),
        "tools": ("epic", "emr", "electronic medical records"),
    },
    "engineering": {
        "titles": (
            "engineer", "design engineer", "mechanical engineer",
            "civil engineer", "electrical engineer",
        ),
        "responsibilities": (
            "cad design", "computer aided design", "design engineering",
            "engineering drawings", "technical drawings", "design specifications",
            "test prototypes", "prototype testing",
        ),
        "tools": ("cad", "autocad", "solidworks", "matlab"),
    },
    "marketing": {
        "titles": ("marketing specialist", "marketing manager", "seo specialist"),
        "responsibilities": (
            "seo campaigns", "search engine optimization", "organic search",
            "content marketing", "marketing campaigns", "campaign performance",
            "digital marketing",
        ),
        "tools": ("seo", "google analytics", "google ads", "semrush"),
    },
    "accounting_finance": {
        "titles": ("accountant", "bookkeeper", "accounting clerk", "financial analyst"),
        "responsibilities": (
            "bookkeeping", "financial reporting", "financial reports",
            "account reconciliation", "bank reconciliation", "accounts payable",
            "accounts receivable", "month end close",
        ),
        "tools": ("quickbooks", "sap", "excel", "xero"),
    },
    "human_resources": {
        "titles": ("hr specialist", "human resources", "recruiter", "hr manager"),
        "responsibilities": (
            "recruitment", "candidate screening", "employee onboarding",
            "onboard employees", "employee relations", "workforce planning",
            "payroll administration",
        ),
        "tools": ("workday", "greenhouse", "lever", "hris"),
    },
    "sales": {
        "titles": ("sales executive", "sales representative", "account executive"),
        "responsibilities": (
            "lead generation", "client acquisition", "prospect clients",
            "manage sales pipeline", "close deals", "sales negotiations",
            "customer acquisition",
        ),
        "tools": ("salesforce", "hubspot", "crm"),
    },
}

_TOKEN = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)
_DURATION_CLAIM = re.compile(r"\b\d+(?:\.\d+)?\s*(?:years?|months?)\b", re.IGNORECASE)
_TRANSFERABLE_RESPONSIBILITIES = (
    "coordinate projects", "manage project budgets", "budget management",
    "quality assurance", "analyze data", "data analysis", "prepare documentation",
    "stakeholder communication", "customer service", "team leadership",
)
_STOPWORDS = {
    "a", "an", "and", "for", "in", "of", "the", "to", "with", "senior",
    "junior", "lead", "manager", "specialist", "professional",
}


def _contains(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase.casefold())
    return bool(re.search(rf"(?<!\w){escaped}(?!\w)", text.casefold()))


def _matches(text: str, phrases: Sequence[str]) -> list[str]:
    return [phrase for phrase in phrases if _contains(text, phrase)]


def _domains_for_text(text: str, evidence_key: str) -> set[str]:
    domains = set()
    for domain, evidence in _DOMAIN_EVIDENCE.items():
        if _matches(text, evidence[evidence_key]):
            domains.add(domain)
    return domains


def _title_similarity(job_title: str, candidate_title: str) -> float:
    job_tokens = {
        token for token in _TOKEN.findall(job_title.casefold())
        if token not in _STOPWORDS
    }
    candidate_tokens = {
        token for token in _TOKEN.findall(candidate_title.casefold())
        if token not in _STOPWORDS
    }
    if not job_tokens or not candidate_tokens:
        return 0.0
    return round(len(job_tokens & candidate_tokens) / len(job_tokens | candidate_tokens), 2)


def _snippets(source_text: str, terms: Sequence[str]) -> list[str]:
    snippets: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", source_text):
        if any(_contains(sentence, term) for term in terms):
            snippet = sentence.strip()
            if snippet and snippet not in snippets:
                snippets.append(snippet)
    return snippets[:8]


def _subtract_intervals(
    intervals: Sequence[tuple[int, int]],
    exclusions: Sequence[tuple[int, int]],
) -> list[tuple[int, int]]:
    remaining: list[tuple[int, int]] = []
    for start, end in intervals:
        segments = [(start, end)]
        for excluded_start, excluded_end in exclusions:
            next_segments: list[tuple[int, int]] = []
            for segment_start, segment_end in segments:
                if excluded_end <= segment_start or excluded_start >= segment_end:
                    next_segments.append((segment_start, segment_end))
                    continue
                if segment_start < excluded_start:
                    next_segments.append((segment_start, excluded_start))
                if excluded_end < segment_end:
                    next_segments.append((excluded_end, segment_end))
            segments = next_segments
        remaining.extend(segments)
    return remaining


def _merge_months(intervals: Sequence[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    ordered = sorted(intervals)
    total = 0
    start, end = ordered[0]
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + end - start


def _classify_role(
    job_title: str,
    job_text: str,
    required_skills: Sequence[str],
    role: dict[str, Any],
) -> dict[str, Any]:
    source_text = str(role.get("sourceText") or "")
    title = str(role.get("title") or "")
    role_text = " ".join(
        [title, source_text, *(str(item) for item in role.get("responsibilities", []))]
    )
    job_domains = _domains_for_text(job_title + " " + job_text, "titles")
    job_domains |= _domains_for_text(job_title + " " + job_text, "responsibilities")
    job_domains |= _domains_for_text(
        job_title + " " + job_text + " " + " ".join(required_skills), "tools"
    )
    role_domains = _domains_for_text(title, "titles")
    role_domains |= _domains_for_text(role_text, "responsibilities")
    role_domains |= _domains_for_text(role_text, "tools")

    job_responsibilities = {
        phrase
        for domain in job_domains
        for phrase in _DOMAIN_EVIDENCE[domain]["responsibilities"]
        if _contains(job_text, phrase)
    }
    role_responsibilities = {
        phrase
        for domain in role_domains | job_domains
        for phrase in _DOMAIN_EVIDENCE[domain]["responsibilities"]
        if _contains(role_text, phrase)
    }
    matched_responsibilities = sorted(
        (job_responsibilities & role_responsibilities)
        | {
            phrase for phrase in _TRANSFERABLE_RESPONSIBILITIES
            if _contains(job_text, phrase) and _contains(role_text, phrase)
        },
        key=str.casefold,
    )
    matched_requirements = sorted(
        {skill for skill in required_skills if skill.strip() and _contains(role_text, skill.strip())},
        key=str.casefold,
    )
    job_tools = {
        phrase
        for domain in job_domains
        for phrase in _DOMAIN_EVIDENCE[domain]["tools"]
        if _contains(job_title + " " + job_text + " " + " ".join(required_skills), phrase)
    }
    matched_tools = sorted(
        {tool for tool in job_tools if _contains(role_text, tool)}
        | {skill for skill in matched_requirements if _contains(role_text, skill)},
        key=str.casefold,
    )

    if (
        job_domains & role_domains
        and matched_responsibilities
        and (matched_requirements or matched_tools or len(matched_responsibilities) >= 2)
    ):
        status = "direct"
    elif matched_responsibilities:
        status = "transferable"
    elif (
        job_domains and role_domains and job_domains.isdisjoint(role_domains)
        and len(role_responsibilities) >= 2
    ):
        status = "unrelated"
    else:
        status = "insufficient_evidence"

    evidence_terms = sorted(
        set(matched_responsibilities) | set(matched_requirements) | set(matched_tools),
        key=str.casefold,
    )
    return {
        "relevanceStatus": status,
        "matchedJobRequirements": matched_requirements,
        "matchedResponsibilities": matched_responsibilities,
        "matchedRoleTechnologies": matched_tools,
        "supportingEvidenceSnippets": _snippets(source_text, evidence_terms),
        "roleTitleSimilarity": _title_similarity(job_title, title),
        "relevanceExplanation": {
            "direct": "Role-specific duties and corroborating job evidence match.",
            "transferable": "Explicit related duties are present, but direct role evidence is incomplete.",
            "unrelated": "Clear role-specific duties indicate a different domain.",
            "insufficient_evidence": "Available role evidence is not sufficient to determine relevance.",
        }[status],
    }


def _role_interval(role: dict[str, Any]) -> tuple[tuple[int, int] | None, str]:
    if role.get("extractionConfidence") != "high":
        return None, "needs_review"
    source_text = str(role.get("sourceText") or "")
    intervals, _ = _dated_range_months(source_text)
    if len(intervals) == 1:
        return intervals[0], "verified"
    if len(intervals) > 1:
        return None, "ambiguous_dates"
    if _DURATION_CLAIM.search(source_text):
        return None, "needs_review"
    return None, "missing_dates"


def score_job_relevance(
    job_title: str,
    job_description: str,
    required_skills: Sequence[str],
    experience_requirement: str | None,
    employment_evidence: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Return explainable relevance evidence; this function is not used by live scoring."""
    job_text = f"{job_title}\n{job_description}"
    direct_intervals: list[tuple[int, int]] = []
    transferable_intervals: list[tuple[int, int]] = []
    results: list[dict[str, Any]] = []

    for evidence in employment_evidence:
        result = dict(evidence)
        result.update(
            _classify_role(job_title, job_text, required_skills, evidence)
        )
        interval, date_status = _role_interval(evidence)
        duration_months = interval[1] - interval[0] if interval else None
        result["dateEvidence"] = {
            "startDate": evidence.get("startDateEvidence"),
            "endDate": evidence.get("endDateEvidence"),
            "range": (evidence.get("dateEvidence") or {}).get("range"),
            "current": bool(evidence.get("isCurrent")),
            "durationVerificationStatus": date_status,
        }
        result["dateVerificationStatus"] = date_status
        result["supportedDurationMonths"] = duration_months
        result["supportedDirectDurationMonths"] = 0
        result["transferableDurationMonths"] = 0
        result["durationVerificationStatus"] = (
            "verified" if interval else "needs_review"
        )
        if interval and result["relevanceStatus"] == "direct":
            result["supportedDirectDurationMonths"] = duration_months
            direct_intervals.append(interval)
        elif interval and result["relevanceStatus"] == "transferable":
            result["transferableDurationMonths"] = duration_months
            transferable_intervals.append(interval)
        elif result["relevanceStatus"] == "unrelated" and interval:
            result["durationVerificationStatus"] = "not_relevant"
        elif result["relevanceStatus"] == "insufficient_evidence":
            result["durationVerificationStatus"] = "needs_review"
        results.append(result)

    non_overlapping_transferable = _subtract_intervals(
        transferable_intervals, direct_intervals
    )
    review_claims = [
        {
            "sourceText": role.get("sourceText", ""),
            "status": role["durationVerificationStatus"],
        }
        for role in results
        if role["durationVerificationStatus"] == "needs_review"
    ]
    return {
        "relevanceMatcherVersion": RELEVANCE_MATCHER_VERSION,
        "interpretationNotice": (
            "Deterministic heuristic evidence only; not verification of professional qualifications."
        ),
        "jobTitle": job_title,
        "experienceRequirement": experience_requirement,
        "roles": results,
        "totalDirectRelevantMonths": _merge_months(direct_intervals),
        "totalTransferableMonths": _merge_months(non_overlapping_transferable),
        "reviewNeededDurations": review_claims,
        "status": "needs_review" if review_claims else "analyzed",
    }
