import re
from collections.abc import Sequence
from datetime import date
from typing import TypedDict

from app.services.dataset_resources import load_terms


EDUCATION_MAX_SCORE = 20
_LEVEL_RANK = {
    "secondary": 0,
    "higher_secondary": 1,
    "bachelor": 2,
    "master": 3,
    "doctorate": 4,
}

# Canonical degree, accepted spellings, level, and known field.
_DEGREES: tuple[tuple[str, tuple[str, ...], str, str | None], ...] = (
    ("Matriculation", ("matriculation", "matric", "SSC"), "secondary", None),
    ("FSC", ("FSC", "FSc", "FA", "ICS", "ICom", "HSSC", "intermediate"), "higher_secondary", None),
    ("BA", ("BA", "Bachelor of Arts"), "bachelor", "arts"),
    ("BSc", ("BSc", "Bachelor of Science"), "bachelor", "sciences"),
    ("BS", ("BS",), "bachelor", None),
    ("BSCS", ("BSCS", "B.S.C.S."), "bachelor", "computer_science"),
    ("BSSE", ("BSSE", "B.S.S.E."), "bachelor", "software_engineering"),
    ("BSIT", ("BSIT", "B.S.I.T."), "bachelor", "information_technology"),
    ("BBA", ("BBA",), "bachelor", "business"),
    ("BCom", ("BCom", "B.Com"), "bachelor", "commerce_accounting"),
    ("BE", ("BE", "B.E."), "bachelor", "engineering"),
    ("BEng", ("BEng", "B.Eng."), "bachelor", "engineering"),
    ("BTech", ("BTech", "B.Tech"), "bachelor", "engineering"),
    ("LLB", ("LLB", "LL.B."), "bachelor", "law"),
    ("BS Nursing", ("BS Nursing", "Bachelor of Science in Nursing"), "bachelor", "nursing"),
    ("MA", ("MA", "Master of Arts"), "master", "arts"),
    ("MSc", ("MSc", "Master of Science"), "master", "sciences"),
    ("MS", ("MS",), "master", None),
    ("MSCS", ("MSCS", "M.S.C.S."), "master", "computer_science"),
    ("MBA", ("MBA",), "master", "business"),
    ("MCom", ("MCom", "M.Com"), "master", "commerce_accounting"),
    ("MPhil", ("MPhil", "M.Phil"), "master", None),
    ("LLM", ("LLM", "LL.M."), "master", "law"),
    ("PhD", ("PhD", "Ph.D."), "doctorate", None),
    ("MBBS", ("MBBS",), "professional", "medicine"),
    ("BDS", ("BDS",), "professional", "dentistry"),
    ("Pharm-D", ("Pharm-D", "Pharm D", "PharmD"), "professional", "pharmacy"),
    ("DPT", ("DPT",), "professional", "physical_therapy"),
    ("CA", ("CA", "Chartered Accountant"), "professional", "accounting"),
    ("ACCA", ("ACCA",), "professional", "accounting"),
)

_FIELD_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("computer_science", ("computer science", "computer sciences")),
    ("software_engineering", ("software engineering",)),
    ("information_technology", ("information technology", "information tech", "IT")),
    ("medicine", ("medicine", "medical")),
    ("dentistry", ("dentistry", "dental")),
    ("pharmacy", ("pharmacy", "pharmaceutical sciences")),
    ("nursing", ("nursing",)),
    ("business", ("business administration", "business")),
    ("commerce_accounting", ("commerce", "accounting")),
    ("finance", ("finance",)),
    ("law", ("law", "legal studies")),
    ("engineering", ("engineering",)),
    ("arts", ("humanities", "arts")),
    ("sciences", ("science", "sciences")),
    ("education", ("education", "teaching")),
)

_IN_PROGRESS = re.compile(
    r"\b(?:currently\s+pursuing|pursuing|in\s+progress|student|"
    r"expected\s+graduation|expected\s+to\s+graduate|\d+(?:st|nd|rd|th)\s+semester)\b",
    re.IGNORECASE,
)
_EDUCATION_YEAR_RANGE = re.compile(
    r"\b(?P<start>19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*"
    r"(?P<end>19\d{2}|20\d{2})\b",
    re.IGNORECASE,
)
_GENERIC_LEVELS = (
    ("doctorate", re.compile(r"\b(?:doctorate|doctoral|ph\.?d\.?)\b", re.IGNORECASE)),
    ("master", re.compile(r"\b(?:master(?:'s)?|postgraduate)\b", re.IGNORECASE)),
    ("bachelor", re.compile(r"\b(?:bachelor(?:'s)?|undergraduate)\b", re.IGNORECASE)),
    ("higher_secondary", re.compile(r"\b(?:higher\s+secondary|intermediate|HSSC)\b", re.IGNORECASE)),
    ("secondary", re.compile(r"\b(?:secondary|matriculation|matric|SSC)\b", re.IGNORECASE)),
)
_VAGUE_RELEVANCE = re.compile(r"\b(?:relevant|related)\b", re.IGNORECASE)
_DATASET_EDUCATION_TERMS = tuple(
    term for term in load_terms("education_vocabulary") if len(term) <= 80
)


class EducationScore(TypedDict):
    candidateDegree: str | None
    candidateLevel: str | None
    candidateField: str | None
    candidateStatus: str
    requiredDegrees: list[str]
    requiredLevel: str | None
    requiredFields: list[str]
    fieldMatched: bool | None
    matchPercentage: float | None
    educationScore: float | None
    maxScore: int
    status: str


def _alias_regex(alias: str) -> re.Pattern[str]:
    tokens = re.split(r"[\s.-]+", alias.strip())
    body = r"[\s.-]*".join(re.escape(token) for token in tokens if token)
    return re.compile(rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])", re.IGNORECASE)


_DEGREE_PATTERNS = tuple(
    sorted(
        (
            (_alias_regex(alias), canonical, level, field)
            for canonical, aliases, level, field in _DEGREES
            for alias in aliases
        ),
        key=lambda item: len(item[0].pattern),
        reverse=True,
    )
)
_FIELD_PATTERNS = tuple(
    (
        _alias_regex(alias),
        field,
    )
    for field, aliases in _FIELD_ALIASES
    for alias in aliases
)


def _find_degree_mentions(text: str) -> list[tuple[str, str, str | None]]:
    matches: list[tuple[int, int, str, str, str | None]] = []
    for pattern, canonical, level, field in _DEGREE_PATTERNS:
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), canonical, level, field))
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    results: list[tuple[str, str, str | None]] = []
    occupied_until = -1
    seen: set[str] = set()
    for start, end, canonical, level, field in matches:
        if start < occupied_until:
            continue
        occupied_until = end
        if canonical.casefold() not in seen:
            seen.add(canonical.casefold())
            results.append((canonical, level, field))
    return results


def _find_fields(text: str) -> list[str]:
    matches: list[tuple[int, int, str]] = []
    for pattern, field in _FIELD_PATTERNS:
        matches.extend(
            (match.start(), match.end(), field)
            for match in pattern.finditer(text)
        )
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    fields: list[str] = []
    occupied_until = -1
    for start, end, field in matches:
        if start < occupied_until:
            continue
        occupied_until = end
        if field not in fields:
            fields.append(field)
    return fields


def _education_texts(values: Sequence[str | dict[str, str]]) -> list[str]:
    texts: list[str] = []
    for value in values:
        text = value.get("text", "") if isinstance(value, dict) else value
        if isinstance(text, str) and text.strip():
            texts.append(re.sub(r"\s+", " ", text).strip())
    return texts


def _candidate_qualifications(
    education: Sequence[str | dict[str, str]],
) -> list[dict[str, str | None]]:
    qualifications: list[dict[str, str | None]] = []
    for text in _education_texts(education):
        degrees = _find_degree_mentions(text)
        generic_level = next(
            (level for level, pattern in _GENERIC_LEVELS if pattern.search(text)),
            None,
        )
        explicit_fields = _find_fields(text)
        year_range = _EDUCATION_YEAR_RANGE.search(text)
        has_credential = bool(degrees or generic_level)
        future_study_range = bool(
            has_credential
            and year_range
            and int(year_range.group("start")) <= date.today().year
            and int(year_range.group("end")) >= date.today().year
        )
        in_progress = bool(_IN_PROGRESS.search(text)) or future_study_range
        status = "in_progress" if in_progress else "completed"

        if degrees:
            for degree, level, degree_field in degrees:
                fields = explicit_fields or ([degree_field] if degree_field else [])
                qualifications.append(
                    {
                        "degree": degree,
                        "level": level,
                        "field": fields[0] if fields else None,
                        "status": status,
                    }
                )
        elif generic_level:
            qualifications.append(
                {
                    "degree": generic_level.replace("_", " ").title(),
                    "level": generic_level,
                    "field": explicit_fields[0] if explicit_fields else None,
                    "status": status,
                }
            )
        elif explicit_fields:
            qualifications.append(
                {
                    "degree": None,
                    "level": None,
                    "field": explicit_fields[0],
                    "status": status,
                }
            )
        else:
            dataset_term = next(
                (
                    term
                    for term in _DATASET_EDUCATION_TERMS
                    if re.search(
                        rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])",
                        text,
                        re.IGNORECASE,
                    )
                ),
                None,
            )
            if dataset_term:
                qualifications.append(
                    {
                        "degree": dataset_term,
                        "level": None,
                        "field": None,
                        "status": status,
                    }
                )
    return qualifications


def _parse_requirement(requirement: str) -> tuple[list[str], str | None, list[str]] | None:
    if not requirement.strip():
        return None
    if _VAGUE_RELEVANCE.search(requirement) and not _find_fields(requirement):
        return None

    degree_mentions = _find_degree_mentions(requirement)
    required_degrees = [degree for degree, _, _ in degree_mentions]
    fields = _find_fields(requirement)
    for _, _, degree_field in degree_mentions:
        if degree_field and degree_field not in fields:
            fields.append(degree_field)

    level = next(
        (candidate_level for candidate_level, pattern in _GENERIC_LEVELS if pattern.search(requirement)),
        None,
    )
    if level is None and degree_mentions:
        levels = {degree_level for _, degree_level, _ in degree_mentions}
        if len(levels) == 1:
            level = next(iter(levels))
    if level is None:
        return None
    return required_degrees, level, fields


def _fields_relevant(candidate_field: str | None, required_fields: list[str]) -> bool:
    if candidate_field is None:
        return False
    if candidate_field in required_fields:
        return True
    # Commerce qualifications can be accounting-oriented; this is the only
    # deliberately broad domain overlap supported by the current taxonomy.
    return candidate_field == "commerce_accounting" and "commerce_accounting" in required_fields


def _evaluate_qualification(
    qualification: dict[str, str | None],
    required_degrees: list[str],
    required_level: str | None,
    required_fields: list[str],
) -> tuple[float, bool | None]:
    candidate_degree = qualification["degree"]
    candidate_level = qualification["level"]
    candidate_field = qualification["field"]
    candidate_status = qualification["status"] or "unknown"
    exact_degree_match = bool(
        candidate_degree
        and any(candidate_degree.casefold() == degree.casefold() for degree in required_degrees)
    )
    field_matched: bool | None = (
        _fields_relevant(candidate_field, required_fields) if required_fields else None
    )

    professional_requirement = required_level == "professional"
    if professional_requirement:
        if not exact_degree_match:
            return 0.0, field_matched
        return (15.0 if candidate_status == "in_progress" else 20.0), True

    if required_fields:
        if not field_matched or candidate_level not in _LEVEL_RANK or required_level not in _LEVEL_RANK:
            return 0.0, field_matched
        if _LEVEL_RANK[candidate_level] < _LEVEL_RANK[required_level]:
            return 0.0, field_matched
        return (15.0 if candidate_status == "in_progress" else 20.0), True

    if required_level is None or candidate_level not in _LEVEL_RANK or required_level not in _LEVEL_RANK:
        return 0.0, field_matched

    difference = _LEVEL_RANK[candidate_level] - _LEVEL_RANK[required_level]
    if difference >= 0:
        return (15.0 if candidate_status == "in_progress" else 20.0), field_matched
    if difference == -1:
        return 10.0, field_matched
    return 0.0, field_matched


def score_education(
    resume_education: Sequence[str | dict[str, str]],
    required_education: str,
) -> EducationScore:
    parsed_requirement = _parse_requirement(required_education)
    qualifications = _candidate_qualifications(resume_education)

    if parsed_requirement is None:
        return {
            "candidateDegree": qualifications[0]["degree"] if qualifications else None,
            "candidateLevel": qualifications[0]["level"] if qualifications else None,
            "candidateField": qualifications[0]["field"] if qualifications else None,
            "candidateStatus": qualifications[0]["status"] if qualifications else "unknown",
            "requiredDegrees": [],
            "requiredLevel": None,
            "requiredFields": [],
            "fieldMatched": None,
            "matchPercentage": None,
            "educationScore": None,
            "maxScore": EDUCATION_MAX_SCORE,
            "status": "not_scored_no_parseable_requirement",
        }

    required_degrees, required_level, required_fields = parsed_requirement
    if not qualifications:
        return {
            "candidateDegree": None,
            "candidateLevel": None,
            "candidateField": None,
            "candidateStatus": "unknown",
            "requiredDegrees": required_degrees,
            "requiredLevel": required_level,
            "requiredFields": required_fields,
            "fieldMatched": False if required_fields else None,
            "matchPercentage": 0.0,
            "educationScore": 0.0,
            "maxScore": EDUCATION_MAX_SCORE,
            "status": "scored",
        }

    evaluated = [
        (_evaluate_qualification(item, required_degrees, required_level, required_fields), item)
        for item in qualifications
    ]
    ((score, field_matched), candidate) = max(
        evaluated,
        key=lambda value: value[0][0],
    )
    status = "scored_in_progress" if score == 15.0 and candidate["status"] == "in_progress" else "scored"
    return {
        "candidateDegree": candidate["degree"],
        "candidateLevel": candidate["level"],
        "candidateField": candidate["field"],
        "candidateStatus": candidate["status"] or "unknown",
        "requiredDegrees": required_degrees,
        "requiredLevel": required_level,
        "requiredFields": required_fields,
        "fieldMatched": field_matched,
        "matchPercentage": round(score / EDUCATION_MAX_SCORE * 100, 2),
        "educationScore": score,
        "maxScore": EDUCATION_MAX_SCORE,
        "status": status,
    }