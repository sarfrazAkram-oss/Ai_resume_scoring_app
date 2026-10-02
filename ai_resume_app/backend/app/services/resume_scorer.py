import re
from collections.abc import Sequence
from typing import TypedDict


SKILLS_MAX_SCORE = 40
_SEPARATORS = re.compile(r"[,;\n]+")
_SURROUNDING_PUNCTUATION = " \t\r\n,;:()[]{}\"'`!?."
_SKILL_ALIASES = {
    "js": "javascript",
    "nextjs": "next.js",
    "nodejs": "node.js",
    "reactjs": "react",
    "flutter framework": "flutter",
}
_DISPLAY_NAMES = {
    "javascript": "JavaScript",
    "next.js": "Next.js",
    "node.js": "Node.js",
    "react": "React",
    "flutter": "Flutter",
}
EXPERIENCE_MAX_SCORE = 25
_REQUIRED_YEAR_RANGE = re.compile(
    r"\b(?P<minimum>\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*"
    r"(?P<maximum>\d+(?:\.\d+)?)\s*\+?\s*years?\b",
    re.IGNORECASE,
)
_REQUIRED_YEARS = re.compile(
    r"\b(?:minimum\s+)?(?P<years>\d+(?:\.\d+)?)\s*\+?\s*years?\b",
    re.IGNORECASE,
)
_REQUIRED_MONTHS = re.compile(
    r"\b(?:minimum\s+)?(?P<months>\d+(?:\.\d+)?)\s*months?\b",
    re.IGNORECASE,
)
_ZERO_EXPERIENCE_REQUIREMENT = re.compile(
    r"\b(?:fresh\s+graduate|entry\s+level)\b",
    re.IGNORECASE,
)
_DURATION = re.compile(
    r"\b(?P<amount>\d+(?:\.\d+)?)\s*\+?\s*"
    r"(?P<unit>years?|months?)\b",
    re.IGNORECASE,
)
_DATE_RANGE = re.compile(
    r"(?P<start_month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
    r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)\.?\s+(?P<start_year>\d{4})\s*"
    r"(?:-|–|—|to)\s*"
    r"(?P<end_month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
    r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)\.?\s+(?P<end_year>\d{4})",
    re.IGNORECASE,
)
_YEAR_RANGE_ANY = re.compile(
    r"\b(?:19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*"
    r"(?:19\d{2}|20\d{2}|present|current|now)\b",
    re.IGNORECASE,
)
_MONTH_NUMBERS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


class SkillsScore(TypedDict):
    matchedSkills: list[str]
    missingSkills: list[str]
    requiredSkillsCount: int
    matchedSkillsCount: int
    matchPercentage: float | None
    skillsScore: float | None
    maxScore: int
    status: str


class ExperienceScore(TypedDict):
    candidateYears: float
    requiredYears: float | None
    matchPercentage: float | None
    experienceScore: float | None
    maxScore: int
    status: str


def _normalize_skill(value: str) -> tuple[str, str] | None:
    cleaned = value.strip(_SURROUNDING_PUNCTUATION)
    if not cleaned:
        return None

    key = re.sub(r"\s+", " ", cleaned).casefold()
    canonical = _SKILL_ALIASES.get(key, key)
    display = _DISPLAY_NAMES.get(canonical, cleaned)
    return canonical, display


def _skill_items(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        return _SEPARATORS.split(value)
    return [item for item in value if isinstance(item, str)]


def _unique_skills(value: str | Sequence[str]) -> list[tuple[str, str]]:
    unique: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in _skill_items(value):
        normalized = _normalize_skill(item)
        if normalized is None:
            continue
        key, display = normalized
        if key not in seen:
            seen.add(key)
            unique.append((key, display))
    return unique


def score_skills(
    resume_skills: list[str],
    required_skills: str | list[str],
) -> SkillsScore:
    requirements = _unique_skills(required_skills)
    normalized_resume = {key for key, _ in _unique_skills(resume_skills)}

    if not requirements:
        return {
            "matchedSkills": [],
            "missingSkills": [],
            "requiredSkillsCount": 0,
            "matchedSkillsCount": 0,
            "matchPercentage": None,
            "skillsScore": None,
            "maxScore": SKILLS_MAX_SCORE,
            "status": "not_scored_no_requirements",
        }

    matched = [
        display for key, display in requirements if key in normalized_resume
    ]
    missing = [
        display for key, display in requirements if key not in normalized_resume
    ]
    required_count = len(requirements)
    matched_count = len(matched)
    match_percentage = round(matched_count / required_count * 100, 2)
    skills_score = round(matched_count / required_count * SKILLS_MAX_SCORE, 2)

    return {
        "matchedSkills": matched,
        "missingSkills": missing,
        "requiredSkillsCount": required_count,
        "matchedSkillsCount": matched_count,
        "matchPercentage": match_percentage,
        "skillsScore": skills_score,
        "maxScore": SKILLS_MAX_SCORE,
        "status": "scored",
    }


def _parse_required_years(requirement: str) -> float | None:
    if _ZERO_EXPERIENCE_REQUIREMENT.search(requirement):
        return 0.0

    year_range = _REQUIRED_YEAR_RANGE.search(requirement)
    if year_range:
        return float(year_range.group("minimum"))

    years = _REQUIRED_YEARS.search(requirement)
    if years:
        return float(years.group("years"))

    months = _REQUIRED_MONTHS.search(requirement)
    if months:
        return float(months.group("months")) / 12

    return None


def _duration_years(amount: str, unit: str) -> float:
    value = float(amount)
    return value if unit.casefold().startswith("year") else value / 12


def _dated_range_months(
    text: str,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    intervals: list[tuple[int, int]] = []
    covered_spans: list[tuple[int, int]] = []

    for match in _DATE_RANGE.finditer(text):
        start = int(match.group("start_year")) * 12 + _MONTH_NUMBERS[
            match.group("start_month").casefold()
        ]
        end = int(match.group("end_year")) * 12 + _MONTH_NUMBERS[
            match.group("end_month").casefold()
        ]
        if end > start:
            intervals.append((start, end))
            covered_spans.append(match.span())

    for match in _YEAR_RANGE_ANY.finditer(text):
        if any(match.start() < end and match.end() > start for start, end in covered_spans):
            continue
        start_year = int(match.group(0)[:4])
        end_text = re.search(r"(?:19|20)\d{2}", match.group(0)[4:])
        if end_text is None:
            continue
        end_year = int(end_text.group(0))
        start = start_year * 12 + 1
        end = end_year * 12 + 1
        if end > start:
            intervals.append((start, end))
            covered_spans.append(match.span())

    return intervals, covered_spans


def _merge_intervals(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    intervals.sort()
    total_months = 0
    current_start, current_end = intervals[0]
    for start, end in intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total_months += current_end - current_start
            current_start, current_end = start, end
    total_months += current_end - current_start
    return total_months


def _entry_candidate_years(entry_text: str) -> float:
    text = entry_text.strip()
    dated_intervals, date_spans = _dated_range_months(text)
    date_months = _merge_intervals(dated_intervals)

    explicit_durations = [
        _duration_years(match.group("amount"), match.group("unit"))
        for match in _DURATION.finditer(text)
        if not any(
            match.start() < span_end and match.end() > span_start
            for span_start, span_end in date_spans
        )
    ]
    duration_years = max(explicit_durations, default=0.0)

    # Written durations and date ranges often describe the same role. Use one
    # conservative estimate for this entry; separate entries are summed later.
    return max(date_months / 12, duration_years)


def _experience_entries(experience: Sequence[str | dict[str, str]]) -> list[str]:
    entries: list[str] = []
    for entry in experience:
        text = entry.get("text", "") if isinstance(entry, dict) else entry
        if isinstance(text, str) and text.strip():
            entries.append(text.strip())
    return entries


def score_experience(
    resume_experience: Sequence[str | dict[str, str]],
    required_experience: str,
) -> ExperienceScore:
    required_years = _parse_required_years(required_experience)
    entry_years = [_entry_candidate_years(entry) for entry in _experience_entries(resume_experience)]
    candidate_years = round(sum(entry_years), 2)

    if required_years is None:
        return {
            "candidateYears": candidate_years,
            "requiredYears": None,
            "matchPercentage": None,
            "experienceScore": None,
            "maxScore": EXPERIENCE_MAX_SCORE,
            "status": "not_scored_no_parseable_requirement",
        }

    if required_years == 0:
        return {
            "candidateYears": candidate_years,
            "requiredYears": 0.0,
            "matchPercentage": 100.0,
            "experienceScore": float(EXPERIENCE_MAX_SCORE),
            "maxScore": EXPERIENCE_MAX_SCORE,
            "status": "scored_no_experience_required",
        }

    match_percentage = round(min(candidate_years / required_years, 1.0) * 100, 2)
    experience_score = round(
        min(candidate_years / required_years, 1.0) * EXPERIENCE_MAX_SCORE,
        2,
    )
    return {
        "candidateYears": candidate_years,
        "requiredYears": required_years,
        "matchPercentage": match_percentage,
        "experienceScore": experience_score,
        "maxScore": EXPERIENCE_MAX_SCORE,
        "status": "scored",
    }