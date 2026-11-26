import re
from collections.abc import Sequence
from typing_extensions import TypedDict

from app.services.resume_scorer import (
    _SKILL_ALIASES,
    _unique_skills,
)


PROJECTS_MAX_SCORE = 15


class ProjectsScore(TypedDict):
    matchedProjectSkills: list[str]
    missingProjectSkills: list[str]
    requiredSkillsCount: int
    matchedSkillsCount: int
    matchPercentage: float | None
    projectsScore: float | None
    maxScore: int
    status: str


def _project_texts(projects: Sequence[str | dict[str, str]]) -> list[str]:
    texts: list[str] = []
    for project in projects:
        text = project.get("text", "") if isinstance(project, dict) else project
        if isinstance(text, str) and text.strip():
            texts.append(re.sub(r"\s+", " ", text).strip())
    return texts


def _skill_variants(key: str, display: str) -> set[str]:
    variants = {key, display}
    variants.update(
        alias for alias, canonical in _SKILL_ALIASES.items() if canonical == key
    )
    return variants


def _skill_pattern(value: str) -> re.Pattern[str]:
    escaped = re.escape(value)
    if value.casefold() == "c":
        return re.compile(r"(?<![A-Za-z0-9])C(?![A-Za-z0-9+#])", re.IGNORECASE)
    if value.casefold() in {"c++", "c#"}:
        return re.compile(
            rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9+#])",
            re.IGNORECASE,
        )
    if value.casefold() in {"js", "ts"}:
        return re.compile(
            rf"(?<![A-Za-z0-9.]){escaped}(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
    return re.compile(
        rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


def _skill_appears_in_projects(
    key: str,
    display: str,
    project_texts: Sequence[str],
) -> bool:
    patterns = tuple(_skill_pattern(variant) for variant in _skill_variants(key, display))
    return any(
        pattern.search(text)
        for text in project_texts
        for pattern in patterns
    )


def score_projects(
    resume_projects: Sequence[str | dict[str, str]],
    job_title: str,
    required_skills: str | list[str] | None,
    job_description: str,
) -> ProjectsScore:
    # Title and description are accepted for future conservative signals, but
    # this version scores only explicit required-skill evidence in projects.
    _ = job_title, job_description
    requirements = _unique_skills(required_skills or "")

    if not requirements:
        return {
            "matchedProjectSkills": [],
            "missingProjectSkills": [],
            "requiredSkillsCount": 0,
            "matchedSkillsCount": 0,
            "matchPercentage": None,
            "projectsScore": None,
            "maxScore": PROJECTS_MAX_SCORE,
            "status": "not_scored_no_project_requirements",
        }

    project_texts = _project_texts(resume_projects)
    matched = [
        display
        for key, display in requirements
        if _skill_appears_in_projects(key, display, project_texts)
    ]
    matched_keys = {key for key, display in requirements if display in matched}
    missing = [
        display
        for key, display in requirements
        if key not in matched_keys
    ]

    required_count = len(requirements)
    matched_count = len(matched)
    match_percentage = round(matched_count / required_count * 100, 2)
    projects_score = round(matched_count / required_count * PROJECTS_MAX_SCORE, 2)
    return {
        "matchedProjectSkills": matched,
        "missingProjectSkills": missing,
        "requiredSkillsCount": required_count,
        "matchedSkillsCount": matched_count,
        "matchPercentage": match_percentage,
        "projectsScore": projects_score,
        "maxScore": PROJECTS_MAX_SCORE,
        "status": "scored",
    }