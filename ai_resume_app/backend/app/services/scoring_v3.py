"""Version 3 deterministic, evidence-based resume scoring."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.services.education_scorer import score_education
from app.services.job_relevance_scorer import score_job_relevance
from app.services.resume_scorer import _SKILL_ALIASES, _unique_skills


SCORING_MODEL_VERSION = 3
COMPONENT_WEIGHTS = {
    "skills": 40,
    "experience": 25,
    "education": 20,
    "practicalWork": 15,
}

_SKILL_SYNONYMS = {
    "continuous integration and delivery": "ci/cd",
    "continuous integration and deployment": "ci/cd",
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "flutter sdk": "flutter",
    "dart language": "dart",
    "bloc": "bloc",
    "business logic component": "bloc",
    "amazon web services": "aws",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "react.js": "react",
    "reactjs": "react",
}
_SKILL_TEXT_VARIANTS = {
    "rest api": ("rest api", "rest apis", "restful api", "restful apis"),
    "ci/cd": (
        "ci/cd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
    ),
}
_ACTION = re.compile(
    r"\b(?:built|build|created|create|delivered|deliver|developed|develop|"
    r"designed|design|engineered|engineer|implemented|implement|integrated|"
    r"integrate|launched|launch|led|lead|maintained|maintain|migrated|migrate|"
    r"optimized|optimised|optimize|optimise|refactored|refactor|tested|test|"
    r"automated|automate|configured|configure|deployed|deploy|improved|improve|"
    r"contributed|contribute)\b",
    re.IGNORECASE,
)
_COMPLEXITY = re.compile(
    r"\b(?:api|apis|authentication|authorization|database|integration|"
    r"performance|responsive|state management|architecture|synchroni[sz]ation|"
    r"scalable|real.time|ci/cd|automated testing|offline|real-time)\b",
    re.IGNORECASE,
)
_OUTCOME = re.compile(
    r"\b(?:achieved|enabled|improved|increased|reduced|resulting|resulted|"
    r"launched|delivered|supported|streamlined|accelerated|users|downloads|"
    r"adoption|performance|reliability)\b",
    re.IGNORECASE,
)
_EXPERIENCE_YEARS = re.compile(
    r"\b(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>years?|yrs?|months?)\b",
    re.IGNORECASE,
)
_SPLIT_REQUIREMENTS = re.compile(r"[,;\n]+")
_SPLIT_SENTENCES = re.compile(r"(?<=[.!?])\s+|\n+")


def _canonical_skill(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip()).casefold()
    canonical = _SKILL_SYNONYMS.get(
        normalized,
        _SKILL_ALIASES.get(normalized, normalized),
    )
    canonical = _SKILL_SYNONYMS.get(canonical, canonical)
    return re.sub(r"\s+", " ", canonical)


def _contains_term(text: str, phrase: str) -> bool:
    variants = _SKILL_TEXT_VARIANTS.get(phrase, (phrase,))
    return any(
        re.search(
            rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])",
            text.casefold(),
        )
        for variant in variants
    )


def _skill_evidence(
    resume_skills: Sequence[str],
    required_skills: str | Sequence[str] | None,
) -> dict[str, Any]:
    requirements = _unique_skills(required_skills or "")
    evidence: list[dict[str, Any]] = []
    matched_count = 0
    for _, display in requirements:
        canonical = _canonical_skill(display)
        match = next(
            (
                skill
                for skill in resume_skills
                if isinstance(skill, str) and _canonical_skill(skill) == canonical
            ),
            None,
        )
        matched = match is not None
        matched_count += int(matched)
        evidence.append(
            {
                "requirement": display,
                "matched": matched,
                "resumeSkillEvidence": match,
            }
        )
    required_count = len(evidence)
    score = round(matched_count / required_count * 40, 2) if required_count else 0.0
    return {
        "score": score,
        "maxScore": 40,
        "matchedCount": matched_count,
        "requiredCount": required_count,
        "requirements": evidence,
        "reason": (
            "Each distinct saved job skill requirement is counted once; recognized "
            "synonyms share a canonical match and repeated mentions add no credit."
        ),
    }


def _experience_target(
    policy: Mapping[str, Any],
    required_experience: str,
) -> float | None:
    for key in ("experienceYears", "experience_years", "minimumExperienceYears"):
        value = policy.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return max(float(value), 0.0)
        if isinstance(value, str) and value.strip():
            try:
                return max(float(value), 0.0)
            except ValueError:
                pass

    match = _EXPERIENCE_YEARS.search(required_experience or "")
    if not match:
        return None
    amount = float(match.group("value"))
    if match.group("unit").casefold().startswith("month"):
        return amount / 12
    return amount


def _experience_evidence(
    employment: Sequence[dict[str, Any]],
    job_title: str,
    job_description: str,
    required_skills: str | Sequence[str] | None,
    policy: Mapping[str, Any],
    required_experience: str,
) -> dict[str, Any]:
    state = policy.get("experienceRequirement")
    target_years = _experience_target(policy, required_experience)
    if state == "not_applicable" or target_years == 0:
        return {
            "score": 25.0,
            "maxScore": 25,
            "candidateDirectRelevantYears": 0.0,
            "requiredYears": target_years,
            "neutralCredit": True,
            "reason": "No positive experience requirement; neutral full credit.",
            "relevance": None,
        }
    if target_years is None and state in {"required", "preferred"}:
        return {
            "score": 0.0,
            "maxScore": 25,
            "candidateDirectRelevantYears": 0.0,
            "requiredYears": None,
            "neutralCredit": False,
            "reason": "Applicable experience has no valid positive year requirement.",
            "relevance": None,
        }
    if target_years is None:
        return {
            "score": 25.0,
            "maxScore": 25,
            "candidateDirectRelevantYears": 0.0,
            "requiredYears": None,
            "neutralCredit": True,
            "reason": "No positive experience requirement; neutral full credit.",
            "relevance": None,
        }

    relevance = score_job_relevance(
        job_title,
        job_description,
        [display for _, display in _unique_skills(required_skills or "")],
        f"{target_years} years",
        employment,
    )
    direct_months = int(relevance["totalDirectRelevantMonths"])
    relevant_years = round(direct_months / 12, 2)
    score = round(min(relevant_years / target_years, 1.0) * 25, 2)
    return {
        "score": score,
        "maxScore": 25,
        "candidateDirectRelevantYears": relevant_years,
        "requiredYears": target_years,
        "neutralCredit": False,
        "reason": (
            "Only date-range-valid, directly relevant resume-reported experience "
            "is credited; overlapping periods are counted once."
        ),
        "relevance": relevance,
    }


def _qualification_evidence(
    education: Sequence[str | dict[str, str]],
    degree: str | None,
) -> list[str]:
    if not degree:
        return []
    matches: list[str] = []
    suffix = r"(?:'s|s)?" if degree.casefold() in {"master", "bachelor"} else ""
    pattern = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(degree)}{suffix}(?![A-Za-z0-9])",
        re.I,
    )
    for item in education:
        text = item.get("text", "") if isinstance(item, dict) else item
        if isinstance(text, str) and pattern.search(text) and text not in matches:
            matches.append(text.strip())
    return matches[:3]


def _requirement_phrases(value: str | Sequence[str] | None) -> list[str]:
    if isinstance(value, str):
        values = _SPLIT_REQUIREMENTS.split(value)
    elif isinstance(value, Sequence):
        values = [item for item in value if isinstance(item, str)]
    else:
        values = []
    return [value.strip() for value in values if value.strip()]


def _practical_evidence(
    resume_text: str,
    required_skills: str | Sequence[str] | None,
    project_criteria: str | Sequence[str] | None,
) -> dict[str, Any]:
    relevance_phrases = {
        _canonical_skill(display)
        for _, display in _unique_skills(required_skills or "")
    }
    relevance_phrases.update(
        re.sub(r"\s+", " ", phrase).casefold()
        for phrase in _requirement_phrases(project_criteria)
    )
    relevance_phrases.discard("")

    credited: list[dict[str, Any]] = []
    seen: set[str] = set()
    total = 0
    for sentence in _SPLIT_SENTENCES.split(resume_text):
        statement = re.sub(r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s*", "", sentence).strip()
        normalized = re.sub(r"[^a-z0-9]+", " ", statement.casefold()).strip()
        if not statement or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if not _ACTION.search(statement):
            continue
        matched_terms = sorted(
            (
                phrase
                for phrase in relevance_phrases
                if _contains_term(statement, phrase)
            ),
            key=str.casefold,
        )
        if not matched_terms:
            continue
        reasons = [
            "explicit_action_or_contribution",
            "explicit_job_relevant_technical_evidence",
        ]
        points = 3
        if _COMPLEXITY.search(statement):
            reasons.append("implementation_complexity")
            points += 1
        if _OUTCOME.search(statement):
            reasons.append("stated_outcome")
            points += 1
        points = min(points, 5)
        credited.append(
            {
                "statement": statement,
                "matchedJobCriteria": matched_terms,
                "points": points,
                "reasonCodes": reasons,
            }
        )
        total += points

    score = min(total, 15)
    return {
        "score": float(score),
        "maxScore": 15,
        "evidence": credited,
        "reason": (
            "Distinct explicit contributions earn 3 points for an action and "
            "job relevance, plus 1 each for technical complexity and a stated "
            "outcome; capped at 15."
        ),
    }


def score_resume_v3(
    resume_skills: Sequence[str],
    employment_evidence: Sequence[dict[str, Any]],
    resume_education: Sequence[str | dict[str, str]],
    resume_text: str,
    job_title: str,
    required_skills: str | Sequence[str] | None,
    required_experience: str,
    required_education: str,
    job_description: str,
    job_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    policy = job_policy or {}
    skills_applicable = policy.get("skillsRequirement") != "not_applicable"
    education_applicable = policy.get("educationRequirement") != "not_applicable"
    project_criteria = policy.get("projectCriteria")

    skills = (
        _skill_evidence(resume_skills, required_skills or policy.get("requiredSkills"))
        if skills_applicable
        else {
            "score": 0.0,
            "maxScore": 40,
            "matchedCount": 0,
            "requiredCount": 0,
            "requirements": [],
            "reason": "Skills are not applicable and receive zero points under v3.",
        }
    )
    experience = _experience_evidence(
        employment_evidence,
        job_title,
        job_description,
        required_skills or policy.get("requiredSkills"),
        policy,
        required_experience,
    )

    education_result = (
        score_education(
            resume_education,
            required_education or str(policy.get("requiredEducation") or ""),
        )
        if education_applicable
        else {
            "candidateDegree": None,
            "candidateLevel": None,
            "candidateField": None,
            "candidateStatus": "not_applicable",
            "educationScore": 0.0,
            "maxScore": 20,
            "status": "not_applicable",
        }
    )
    education_score = education_result.get("educationScore")
    education_score = (
        float(education_score)
        if isinstance(education_score, (int, float))
        else 0.0
    )
    education = {
        "score": min(max(education_score, 0.0), 20.0),
        "maxScore": 20,
        "qualification": education_result.get("candidateDegree"),
        "level": education_result.get("candidateLevel"),
        "field": education_result.get("candidateField"),
        "status": education_result.get("candidateStatus"),
        "evidence": _qualification_evidence(
            resume_education,
            education_result.get("candidateDegree"),
        ),
        "reason": (
            "Education marks use only extracted qualification level and field; "
            "an absent or non-matching qualification receives zero."
            if education_applicable
            else "Education is not applicable and receives zero points under v3."
        ),
    }
    practical_work = _practical_evidence(
        resume_text,
        required_skills or policy.get("requiredSkills"),
        project_criteria,
    )

    total = round(
        float(skills["score"])
        + float(experience["score"])
        + float(education["score"])
        + float(practical_work["score"]),
        2,
    )
    return {
        "scoringModelVersion": SCORING_MODEL_VERSION,
        "score": min(max(total, 0.0), 100.0),
        "maxScore": 100,
        "components": {
            "skills": skills,
            "experience": experience,
            "education": education,
            "practicalWork": practical_work,
        },
        "jobScoringPolicyVersion": policy.get("scoringPolicyVersion"),
    }
