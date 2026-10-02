"""Run a deterministic three-candidate ranking demonstration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.final_scorer import score_resume


JOB = {
    "job_title": "Flutter Developer",
    "required_skills": "Flutter, Dart, Firebase, REST API",
    "required_experience": "2 years",
    "required_education": "BSCS or BSSE",
    "job_description": "Build and maintain Flutter applications.",
}

CANDIDATES = [
    {
        "candidate": "A",
        "resume_skills": ["Flutter", "Dart", "Firebase", "REST API"],
        "resume_experience": [{"text": "Flutter Developer - 4 years"}],
        "resume_education": [{"text": "Completed BSSE"}],
        "resume_projects": [{"text": "Flutter Dart Firebase REST API app"}],
    },
    {
        "candidate": "B",
        "resume_skills": ["Flutter", "Dart"],
        "resume_experience": [{"text": "Flutter Developer - 1 year"}],
        "resume_education": [{"text": "BSSE, 7th semester"}],
        "resume_projects": [{"text": "Flutter Dart mobile app"}],
    },
    {
        "candidate": "C",
        "resume_skills": ["MBBS"],
        "resume_experience": [{"text": "Doctor - 5 years"}],
        "resume_education": [{"text": "Completed MBBS"}],
        "resume_projects": [{"text": "Clinical medicine project"}],
    },
]


def run_demo() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for candidate in CANDIDATES:
        score = score_resume(
            **{key: value for key, value in candidate.items() if key != "candidate"},
            **JOB,
        )
        results.append(
            {
                "candidate": candidate["candidate"],
                "skillsScore": score["skills"]["skillsScore"],
                "experienceScore": score["experience"]["experienceScore"],
                "educationScore": score["education"]["educationScore"],
                "projectsScore": score["projects"]["projectsScore"],
                "finalScore": score["finalScore"],
            }
        )
    return sorted(results, key=lambda row: row["finalScore"] or -1, reverse=True)


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))