from collections.abc import Sequence
from typing import TypedDict

from app.services.education_scorer import EducationScore, score_education
from app.services.project_scorer import ProjectsScore, score_projects
from app.services.resume_scorer import (
    ExperienceScore,
    SkillsScore,
    score_experience,
    score_skills,
)


FINAL_MAX_SCORE = 100


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
) -> FinalResumeScore:
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