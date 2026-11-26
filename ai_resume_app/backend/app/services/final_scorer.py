import re
from collections.abc import Mapping, Sequence
from typing import Any

from typing_extensions import TypedDict

from app.services.education_scorer import EducationScore, score_education
from app.services.project_scorer import ProjectsScore, score_projects
from app.services.resume_scorer import (
    ExperienceScore,
    SkillsScore,
    score_experience,
    score_skills,
)


FINAL_MAX_SCORE = 100
_COMPONENT_NAMES = (
    "skills",
    "experience",
    "education",
    "projects",
)
_DEFAULT_COMPONENT_WEIGHTS = {
    "skills": 40,
    "experience": 25,
    "education": 20,
    "projects": 15,
}
class FinalResumeScore(TypedDict):
    skills: SkillsScore
    experience: ExperienceScore
    education: EducationScore
    projects: ProjectsScore
    earnedScore: float
    availableMaxScore: int
    finalScore: float | None
    maxScore: int
    status: str


def _policy_component_state(policy: Mapping[str, Any] | None, key: str) -> str:
    if not policy:
        return "required"
    value = policy.get(key)
    if not isinstance(value, str) or value not in {
        "required",
        "preferred",
        "not_applicable",
    }:
        raise ValueError(f"Invalid or missing scoring applicability: {key}")
    return value


def _experience_requirement_value(policy: Mapping[str, Any] | None, fallback: str) -> str:
    if not policy:
        return fallback
    for key in ("experienceYears", "experience_years", "minimumExperienceYears", "minimum_experience_years"):
        value = policy.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback


def _project_requirement_value(policy: Mapping[str, Any] | None, fallback: str | list[str] | None) -> str | list[str] | None:
    if not policy:
        return fallback
    for key in ("projectCriteria", "project_criteria", "projectsCriteria", "projects_criteria"):
        value = policy.get(key)
        if value not in (None, ""):
            return value
    for key in ("requiredProjects", "required_projects"):
        value = policy.get(key)
        if value not in (None, ""):
            return value
    return fallback


def _parse_year_count(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"(?P<years>\d+(?:\.\d+)?)\s*(?:years?|yrs?)", text, re.IGNORECASE)
    if match:
        return float(match.group("years"))
    match = re.search(r"(?P<months>\d+(?:\.\d+)?)\s*months?", text, re.IGNORECASE)
    if match:
        return float(match.group("months")) / 12
    try:
        return float(text)
    except ValueError:
        return None


def _score_experience_for_policy(
    resume_experience: Sequence[str | dict[str, str]],
    required_experience: str,
    job_policy: Mapping[str, Any] | None,
    requirement_state: str,
) -> ExperienceScore:
    if requirement_state == "not_applicable":
        return {
            "candidateYears": 0.0,
            "requiredYears": None,
            "matchPercentage": None,
            "experienceScore": None,
            "maxScore": 0,
            "status": "not_applicable",
        }

    effective_value = _experience_requirement_value(job_policy, required_experience)
    if requirement_state == "preferred":
        if not effective_value or not str(effective_value).strip():
            raise ValueError("Applicable preferred experience requires target years")
        target_years = _parse_year_count(effective_value)
        if target_years is None or target_years <= 0:
            raise ValueError("Applicable preferred experience requires positive target years")
        candidate_years = score_experience(resume_experience, "")["candidateYears"]
        match_percentage = round(min(candidate_years / target_years, 1.0) * 100, 2)
        experience_score = round(min(candidate_years / target_years, 1.0) * 25, 2)
        return {
            "candidateYears": candidate_years,
            "requiredYears": target_years,
            "matchPercentage": match_percentage,
            "experienceScore": experience_score,
            "maxScore": 25,
            "status": "scored_preferred",
        }

    parsed_years = _parse_year_count(effective_value)
    if parsed_years is None or parsed_years <= 0:
        raise ValueError("Applicable experience requires positive target years")
    return score_experience(resume_experience, f"{parsed_years} years")


def score_resume_with_policy(
    resume_skills: list[str],
    resume_experience: Sequence[str | dict[str, str]],
    resume_education: Sequence[str | dict[str, str]],
    resume_projects: Sequence[str | dict[str, str]],
    job_title: str,
    required_skills: str | list[str] | None,
    required_experience: str,
    required_education: str,
    job_description: str,
    job_policy: Mapping[str, Any] | None = None,
) -> FinalResumeScore:
    policy = job_policy or {}
    skills_requirement = _policy_component_state(policy, "skillsRequirement")
    experience_requirement = _policy_component_state(policy, "experienceRequirement")
    education_requirement = _policy_component_state(policy, "educationRequirement")
    projects_requirement = _policy_component_state(policy, "projectsRequirement")

    if skills_requirement == "not_applicable":
        skills = {
            "matchedSkills": [],
            "missingSkills": [],
            "requiredSkillsCount": 0,
            "matchedSkillsCount": 0,
            "matchPercentage": None,
            "skillsScore": None,
            "maxScore": 0,
            "status": "not_applicable",
        }
    else:
        skill_criteria = required_skills or policy.get("requiredSkills") or ""
        if not str(skill_criteria).strip():
            raise ValueError("Applicable skills criteria are missing")
        skills = score_skills(resume_skills, skill_criteria)

    experience = _score_experience_for_policy(
        resume_experience,
        required_experience,
        policy,
        experience_requirement,
    )

    if education_requirement == "not_applicable":
        education = {
            "candidateDegree": None,
            "candidateLevel": None,
            "candidateField": None,
            "candidateStatus": "not_applicable",
            "requiredDegrees": [],
            "requiredLevel": None,
            "requiredFields": [],
            "fieldMatched": None,
            "matchPercentage": None,
            "educationScore": None,
            "maxScore": 0,
            "status": "not_applicable",
        }
    else:
        education_criteria = required_education or policy.get("requiredEducation") or ""
        if not str(education_criteria).strip():
            raise ValueError("Applicable education criteria are missing")
        education = score_education(resume_education, education_criteria)

    if projects_requirement == "not_applicable":
        projects = {
            "matchedProjectSkills": [],
            "missingProjectSkills": [],
            "requiredSkillsCount": 0,
            "matchedSkillsCount": 0,
            "matchPercentage": None,
            "projectsScore": None,
            "maxScore": 0,
            "status": "not_applicable",
        }
    else:
        explicit_project_criteria = _project_requirement_value(
            policy,
            None if policy else required_skills,
        )
        if not explicit_project_criteria or (
            isinstance(explicit_project_criteria, str)
            and not explicit_project_criteria.strip()
        ):
            raise ValueError("Applicable project criteria are missing")
        projects = score_projects(
            resume_projects,
            job_title,
            explicit_project_criteria,
            job_description,
        )

    components: dict[str, Mapping[str, Any]] = {
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
    }
    earned_score = 0.0
    available_max_score = 0
    for name in _COMPONENT_NAMES:
        component = components[name]
        requirement = {
            "skills": skills_requirement,
            "experience": experience_requirement,
            "education": education_requirement,
            "projects": projects_requirement,
        }[name]
        if requirement == "not_applicable":
            continue
        score_field = f"{name}Score"
        component_score = component.get(score_field)
        if not isinstance(component_score, (int, float)):
            raise ValueError(f"Applicable {name} category could not be scored")
        earned_score += float(component_score)
        available_max_score += _DEFAULT_COMPONENT_WEIGHTS[name]
    earned_score = round(earned_score, 2)

    if available_max_score == 0:
        final_score = None
        status = "not_scored_no_requirements"
    else:
        final_score = round(
            min(earned_score / available_max_score * FINAL_MAX_SCORE, FINAL_MAX_SCORE),
            2,
        )
        status = "scored"

    return {
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "earnedScore": earned_score,
        "availableMaxScore": available_max_score,
        "finalScore": final_score,
        "maxScore": FINAL_MAX_SCORE,
        "status": status,
    }


def score_resume(
    resume_skills: list[str],
    resume_experience: Sequence[str | dict[str, str]],
    resume_education: Sequence[str | dict[str, str]],
    resume_projects: Sequence[str | dict[str, str]],
    job_title: str,
    required_skills: str | list[str] | None,
    required_experience: str,
    required_education: str,
    job_description: str,
    job_policy: Mapping[str, Any] | None = None,
) -> FinalResumeScore:
    if job_policy:
        return score_resume_with_policy(
            resume_skills,
            resume_experience,
            resume_education,
            resume_projects,
            job_title,
            required_skills,
            required_experience,
            required_education,
            job_description,
            job_policy=job_policy,
        )
    skills = score_skills(resume_skills, required_skills or "")
    experience = score_experience(resume_experience, required_experience)
    education = score_education(resume_education, required_education)
    projects = score_projects(
        resume_projects,
        job_title,
        required_skills,
        job_description,
    )

    components = (skills, experience, education, projects)
    score_fields = ("skillsScore", "experienceScore", "educationScore", "projectsScore")
    scored_pairs = [
        (component, score_field)
        for component, score_field in zip(components, score_fields, strict=True)
        if isinstance(component[score_field], (int, float))
    ]
    earned_score = round(
        sum(float(component[score_field]) for component, score_field in scored_pairs),
        2,
    )
    available_max_score = sum(int(component["maxScore"]) for component, _ in scored_pairs)

    if available_max_score == 0:
        final_score = None
        status = "not_scored_no_requirements"
    else:
        final_score = round(
            min(earned_score / available_max_score * FINAL_MAX_SCORE, FINAL_MAX_SCORE),
            2,
        )
        status = "scored"

    return {
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "earnedScore": earned_score,
        "availableMaxScore": available_max_score,
        "finalScore": final_score,
        "maxScore": FINAL_MAX_SCORE,
        "status": status,
    }