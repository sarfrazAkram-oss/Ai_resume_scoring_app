from bisect import bisect_right
import re
from typing import Any

from app.services.dataset_resources import load_terms
from app.services.resume_scorer import (
    _DATE_RANGE,
    _YEAR_RANGE_ANY,
    _dated_range_months,
    _unique_skills,
)


def _normalize_heading(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def _heading_pattern(heading: str) -> str:
    tokens = re.split(r"[\s:_-]+", heading.strip())
    return r"[\s:_-]*".join(re.escape(token) for token in tokens if token)


# Add or replace entries here when the project skills dataset is ready.
SKILLS_BY_CATEGORY: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "programming_languages": (
        ("Python", ("python",)),
        ("Java", ("java",)),
        ("JavaScript", ("javascript", "js")),
        ("TypeScript", ("typescript", "ts")),
        ("C++", ("c++", "cpp")),
        ("C#", ("c#", "c sharp", "csharp")),
        ("C", ("c",)),
        ("Dart", ("dart",)),
        ("Go", ("golang", "go")),
        ("Rust", ("rust",)),
        ("Kotlin", ("kotlin",)),
        ("Swift", ("swift",)),
        ("PHP", ("php",)),
        ("Ruby", ("ruby",)),
        ("R", ("r programming",)),
        ("Bash", ("bash", "shell scripting")),
    ),
    "mobile_development": (
        ("Flutter", ("flutter",)),
        ("React Native", ("react native",)),
        ("Android", ("android",)),
        ("iOS", ("ios",)),
        ("Jetpack Compose", ("jetpack compose",)),
        ("Provider", ("provider",)),
    ),
    "frontend": (
        ("React", ("react",)),
        ("Next.js", ("next.js", "nextjs", "next js")),
        ("Angular", ("angular",)),
        ("Vue.js", ("vue.js", "vuejs", "vue js")),
        ("HTML", ("html",)),
        ("CSS", ("css",)),
        ("Tailwind CSS", ("tailwind css", "tailwind")),
        ("Bootstrap", ("bootstrap",)),
        ("Sass", ("sass", "scss")),
    ),
    "backend": (
        ("Node.js", ("node.js", "nodejs", "node js")),
        ("Express", ("express.js", "express js", "express")),
        ("FastAPI", ("fastapi", "fast api")),
        ("Flask", ("flask",)),
        ("Django", ("django",)),
        ("Spring Boot", ("spring boot",)),
        ("ASP.NET", ("asp.net", "asp net")),
        ("REST API", ("rest api", "restful api")),
        ("GraphQL", ("graphql",)),
    ),
    "databases": (
        ("SQL", ("sql",)),
        ("MySQL", ("mysql",)),
        ("PostgreSQL", ("postgresql", "postgres")),
        ("MongoDB", ("mongodb", "mongo db")),
        ("SQLite", ("sqlite",)),
        ("Redis", ("redis",)),
        ("Firebase", ("firebase",)),
        ("Supabase", ("supabase",)),
    ),
    "ai_ml": (
        ("Machine Learning", ("machine learning",)),
        ("Deep Learning", ("deep learning",)),
        ("TensorFlow", ("tensorflow",)),
        ("PyTorch", ("pytorch",)),
        ("scikit-learn", ("scikit-learn", "scikit learn", "sklearn")),
        ("Natural Language Processing", ("natural language processing", "nlp")),
        ("Computer Vision", ("computer vision",)),
        ("Pandas", ("pandas",)),
        ("NumPy", ("numpy",)),
    ),
    "cloud": (
        ("AWS", ("aws", "amazon web services")),
        ("Microsoft Azure", ("microsoft azure", "azure")),
        ("Google Cloud", ("google cloud", "gcp")),
        ("Docker", ("docker",)),
        ("Kubernetes", ("kubernetes", "k8s")),
        ("CI/CD", ("ci/cd", "continuous integration", "continuous deployment")),
    ),
    "development_tools": (
        ("Git", ("git",)),
        ("GitHub", ("github",)),
        ("GitLab", ("gitlab",)),
        ("Jira", ("jira",)),
        ("Linux", ("linux",)),
        ("VS Code", ("vs code", "visual studio code")),
        ("Postman", ("postman",)),
    ),
    "professional_skills": (
        ("Human Resources", ("human resources", "HR")),
        (
            "Customer Relationship Management",
            ("customer relationship management", "CRM"),
        ),
        (
            "Search Engine Optimization",
            ("search engine optimization", "SEO"),
        ),
        (
            "Electronic Medical Records",
            ("electronic medical records", "EMR"),
        ),
        (
            "Computer-Aided Design",
            ("computer-aided design", "computer aided design", "CAD"),
        ),
    ),
}

SECTION_HEADINGS: dict[str, tuple[str, ...]] = {
    "experience": (
        "EXPERIENCE",
        "WORK EXPERIENCE",
        "PROFESSIONAL EXPERIENCE",
        "EMPLOYMENT",
        "EMPLOYMENT HISTORY",
        "INTERNSHIP",
        "INTERNSHIPS",
    ),
    "education": (
        "EDUCATION",
        "ACADEMIC BACKGROUND",
        "ACADEMIC QUALIFICATION",
        "ACADEMIC QUALIFICATIONS",
        "EDUCATIONAL BACKGROUND",
        "QUALIFICATIONS",
    ),
    "projects": (
        "PROJECTS",
        "ACADEMIC PROJECTS",
        "PERSONAL PROJECTS",
        "RELEVANT PROJECTS",
        "SELECTED PROJECTS",
        "KEY PROJECTS",
        "PROJECT HIGHLIGHTS",
        "UNIVERSITY PROJECTS",
        "PROJECT EXPERIENCE",
        "PROJECTS & EXPERIENCE",
    ),
    "skills": (
        "SKILLS",
        "TECHNICAL SKILLS",
        "CORE SKILLS",
        "TECHNOLOGIES",
        "COMPUTER SKILLS",
    ),
}

_SECTION_BY_HEADING = {
    _normalize_heading(heading): section
    for section, headings in SECTION_HEADINGS.items()
    for heading in headings
}
_OTHER_SECTION_HEADINGS = (
    "SUMMARY",
    "PROFESSIONAL SUMMARY",
    "PROFILE",
    "CAREER OBJECTIVE",
    "OBJECTIVE",
    "CERTIFICATIONS",
    "AWARDS",
    "ACHIEVEMENTS",
    "PUBLICATIONS",
    "VOLUNTEER EXPERIENCE",
    "LANGUAGES",
    "INTERESTS",
    "REFERENCES",
)
_HEADING_PATTERNS: tuple[tuple[str, str], ...] = tuple(
    sorted(
        (
            (
                _heading_pattern(heading),
                section,
            )
            for section, headings in SECTION_HEADINGS.items()
            for heading in headings
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
)
_HEADING_PATTERNS += tuple(
    (
        _heading_pattern(heading),
        "",
    )
    for heading in _OTHER_SECTION_HEADINGS
)
_HEADING_REGEXES = tuple(
    (re.compile(rf"(?<![A-Za-z0-9]){pattern}(?![A-Za-z0-9])", re.IGNORECASE), section)
    for pattern, section in _HEADING_PATTERNS
)
_BULLET_PREFIX = re.compile(r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s*")
_DATE_PREFIX = re.compile(
    r"^\s*(?:\d{4}\s*(?:-|–|—|to)\s*(?:\d{4}|present|current)|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4})\b",
    re.IGNORECASE,
)
_EMPLOYMENT_TITLE_TERMS = (
    "accountant", "accounting", "analyst", "architect", "assistant",
    "developer", "designer", "engineer", "executive", "hr", "human resources",
    "intern", "manager", "marketer", "marketing", "nurse", "nursing",
    "recruiter", "sales", "seo", "technician",
)
_EMPLOYMENT_TOOL_TERMS = (
    "aws", "azure", "cad", "docker", "emr", "epic", "excel", "flutter",
    "google analytics", "jira", "kubernetes", "matlab", "mysql", "python",
    "quickbooks", "react", "salesforce", "sap", "sql", "tableau",
)
_EMPLOYMENT_TITLE_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in _EMPLOYMENT_TITLE_TERMS) + r")\b",
    re.IGNORECASE,
)
_EMPLOYMENT_TOOL_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in _EMPLOYMENT_TOOL_TERMS) + r")\b",
    re.IGNORECASE,
)
_EMPLOYMENT_ACTION_PREFIX = re.compile(
    r"^\s*(?:assisted|built|created|delivered|developed|generated|"
    r"implemented|improved|led|maintained|managed|performed|provided|"
    r"supported|coordinated|administered|analyzed|conducted|worked)\b",
    re.IGNORECASE,
)
_PROJECT_TITLE_LINE = re.compile(
    r"^\s*(?:project\s+(?:\d+|[A-Z])\s*[:#.-]|"
    r"[A-Z][\w .'+#-]{1,60}\s+(?:\||–|—|-)\s+\S)",
    re.IGNORECASE,
)
_EDUCATION_EVIDENCE = re.compile(
    r"\b(?:bachelor(?:'s|s)?|bs(?:cs|se)?|bsc|master(?:'s|s)?|ms(?:cs|se)?|msc|"
    r"matric|fsc|intermediate|degree|(?:\d+(?:st|nd|rd|th)\s+)?semester|"
    r"university|college)\b",
    re.IGNORECASE,
)
_STRONG_EDUCATION_EVIDENCE = re.compile(
    r"\b(?:bachelor(?:'s|s)?|bs(?:cs|se)?|bsc|master(?:'s|s)?|ms(?:cs|se)?|msc|"
    r"matric|fsc|intermediate|degree|(?:\d+(?:st|nd|rd|th)\s+)?semester)\b",
    re.IGNORECASE,
)
_EXPERIENCE_EVIDENCE = re.compile(
    r"\b(?:intern(?:ship)?s?|software\s+engineer|developer|engineer|employment|"
    r"experience|company|\d+\s*\+?\s*(?:months?|years?))\b",
    re.IGNORECASE,
)
_PROJECT_LANGUAGE = re.compile(
    r"\b(?:project|built|developed|created|designed|implemented|"
    r"application|prototype|team\s+leader)\b",
    re.IGNORECASE,
)
_SKILL_EVIDENCE = re.compile(
    r"\b(?:proficient\s+(?:in|with)|skilled\s+(?:in|with)|expert(?:ise)?\s+(?:in|with)|"
    r"knowledge\s+of|experience\s+(?:with|in)|"
    r"experienced\s+in|worked\s+with|working\s+with|built\s+with|developed\s+with|"
    r"implemented\s+with|implemented\s+using|created\s+with|created\s+using|"
    r"programmed\s+in|hands-on\s+with|used|using)\b",
    re.IGNORECASE,
)
_SKILL_POST_EVIDENCE = re.compile(
    r"^\s*(?:(?:is|was|were|has\s+been|have\s+been)\s+)?"
    r"(?:used|applied|implemented|developed|programmed|deployed|maintained|built)\b",
    re.IGNORECASE,
)


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _alias_pattern(alias: str) -> re.Pattern[str]:
    escaped_alias = re.escape(alias)
    if alias.casefold() in {"js", "ts"}:
        return re.compile(
            rf"(?<![A-Za-z0-9.]){escaped_alias}(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
    if alias.casefold() == "c":
        return re.compile(r"(?<![A-Za-z0-9])C(?![A-Za-z0-9+#])", re.IGNORECASE)
    if alias.casefold() in {"c++", "c#"}:
        return re.compile(
            rf"(?<![A-Za-z0-9]){escaped_alias}(?![A-Za-z0-9+#])",
            re.IGNORECASE,
        )
    return re.compile(
        rf"(?<![A-Za-z0-9]){escaped_alias}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


_SKILL_PATTERNS = tuple(
    (canonical, _alias_pattern(alias))
    for entries in SKILLS_BY_CATEGORY.values()
    for canonical, aliases in entries
    for alias in aliases
)
_DATASET_SKILL_PATTERNS = tuple(
    (term, re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE))
    for term in load_terms("skills_vocabulary")
)
_DATASET_EXPERIENCE_PATTERNS = tuple(
    re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE)
    for term in load_terms("experience_vocabulary")
    if len(term) <= 60
)
_ALL_SKILL_PATTERNS = (*_SKILL_PATTERNS, *_DATASET_SKILL_PATTERNS)


def extract_skills(text: str) -> list[str]:
    found: list[tuple[int, str]] = []
    active_section: str | None = None
    offset = 0
    candidate_starts: list[int] = []
    candidate_offsets: list[int] = []
    candidate_data: list[tuple[str, str | None]] = []
    candidate_lines: list[str] = []
    candidate_length = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        matches = [
            (match, section)
            for match, section in _line_heading_matches(line)
            if _is_embedded_heading(line, match, section)
        ]
        if matches:
            section = matches[-1][1]
            active_section = section or None
        heading_only = bool(
            matches
            and not line[matches[-1][0].end():].lstrip(" \t:").strip()
        )
        post_evidence = re.search(
            r"\b(?:is|was|were|has\s+been|have\s+been)?\s*"
            r"(?:used|applied|implemented|developed|programmed|deployed|"
            r"maintained|built)\b",
            line,
            re.IGNORECASE,
        )
        if (
            not heading_only
            and (
                active_section == "skills"
                or _SKILL_EVIDENCE.search(line)
                or post_evidence
            )
        ):
            candidate_starts.append(candidate_length)
            candidate_offsets.append(offset)
            candidate_data.append((line, active_section))
            candidate_lines.append(line)
            candidate_length += len(line) + 1
        offset += len(raw_line)

    candidate_text = "\n".join(candidate_lines)
    for canonical, pattern in _ALL_SKILL_PATTERNS:
        for match in pattern.finditer(candidate_text):
            line_index = bisect_right(candidate_starts, match.start()) - 1
            line, section = candidate_data[line_index]
            relative_start = match.start() - candidate_starts[line_index]
            prefix = line[max(0, relative_start - 70):relative_start]
            evidence = any(
                len(prefix[evidence_match.end():]) <= 55
                and not re.search(r"[.!?;]", prefix[evidence_match.end():])
                for evidence_match in _SKILL_EVIDENCE.finditer(prefix)
            )
            suffix = line[relative_start + len(match.group()):]
            if (
                section == "skills"
                or evidence
                or _SKILL_POST_EVIDENCE.search(suffix)
            ):
                found.append((candidate_offsets[line_index] + relative_start, canonical))
                break

    unique: list[str] = []
    seen: set[str] = set()
    for _, candidate in sorted(found, key=lambda item: (item[0], item[1].casefold())):
        normalized = _unique_skills([candidate])
        if normalized and normalized[0][0] not in seen:
            seen.add(normalized[0][0])
            unique.append(normalized[0][1])
    return unique


def _split_camel_case_boundaries(line: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", line)


def _line_heading_matches(line: str) -> list[tuple[re.Match[str], str]]:
    matches: list[tuple[re.Match[str], str]] = []
    for pattern, section in _HEADING_REGEXES:
        matches.extend((match, section) for match in pattern.finditer(line))
    matches.sort(key=lambda item: (item[0].start(), -len(item[0].group())))

    non_overlapping: list[tuple[re.Match[str], str]] = []
    last_end = -1
    for match, section in matches:
        if match.start() >= last_end:
            non_overlapping.append((match, section))
            last_end = match.end()
    return non_overlapping


def _is_embedded_heading(
    line: str,
    match: re.Match[str],
    section: str,
) -> bool:
    prefix = line[: match.start()]
    suffix = line[match.end() :]
    if not prefix.strip() or suffix.lstrip().startswith(":"):
        return True
    if section == "education":
        return bool(_EDUCATION_EVIDENCE.search(suffix))
    if section == "experience":
        return bool(_EXPERIENCE_EVIDENCE.search(suffix))
    if section == "projects":
        return prefix.rstrip().endswith((".", ";", "|", "•"))
    return False


def _section_blocks(lines: list[str]) -> list[dict[str, str]]:
    blocks: list[str] = []
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            block = _normalize_whitespace(" ".join(current_lines))
            if block:
                blocks.append(block)
            current_lines.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        is_bullet = bool(_BULLET_PREFIX.match(stripped))
        is_date = bool(_DATE_PREFIX.match(stripped))
        if current_lines and (is_bullet or is_date):
            flush()
        cleaned = _BULLET_PREFIX.sub("", stripped)
        if cleaned:
            current_lines.append(cleaned)

    flush()
    return [{"text": block} for block in blocks]


def _employment_header(text: str) -> bool:
    has_date = bool(_dated_range_months(text)[0])
    has_title = bool(_EMPLOYMENT_TITLE_RE.search(text))
    has_employer_separator = bool(re.search(r"\b(?:at|@)\s+[A-Z]", text))
    return has_title and not _EMPLOYMENT_ACTION_PREFIX.search(text) and (
        has_date or has_employer_separator or len(text.split()) <= 7
    )


def _without_date_ranges(text: str) -> str:
    text = _DATE_RANGE.sub("", text)
    return _YEAR_RANGE_ANY.sub("", text).strip(" \t,;|–—-")


def _employment_date_evidence(text: str) -> dict[str, Any]:
    matches = list(_DATE_RANGE.finditer(text))
    if not matches:
        matches = list(_YEAR_RANGE_ANY.finditer(text))
    if len(matches) != 1:
        return {
            "startDate": None,
            "endDate": None,
            "current": False,
            "range": None,
            "status": "missing_dates" if not matches else "ambiguous_dates",
        }

    match = matches[0]
    if "start_month" in match.groupdict():
        start = f"{match.group('start_month')} {match.group('start_year')}"
        end = (
            match.group("end_current")
            or f"{match.group('end_month')} {match.group('end_year')}"
        )
        current = bool(match.group("end_current"))
    else:
        start = match.group(0)[:4]
        end = match.group("end_year")
        current = end.casefold() in {"present", "current", "now"}

    intervals, _ = _dated_range_months(match.group(0))
    valid = len(intervals) == 1
    return {
        "startDate": start,
        "endDate": end,
        "current": current,
        "range": match.group(0),
        "status": "verified" if valid else "ambiguous_dates",
    }


def _employment_record(lines: list[str], confident_header: bool) -> dict[str, Any]:
    source_text = "\n".join(line.strip() for line in lines if line.strip())
    header = next(
        (
            _without_date_ranges(line)
            for line in lines
            if _without_date_ranges(line)
            and (
                _EMPLOYMENT_TITLE_RE.search(_without_date_ranges(line))
                or re.search(r"\b(?:at|@)\s+[A-Z]", _without_date_ranges(line))
            )
        ),
        "",
    )
    date_evidence = _employment_date_evidence(source_text)

    title: str | None = None
    employer: str | None = None
    if header and confident_header:
        separator = re.search(r"\s+(?:at|@)\s+", header, re.IGNORECASE)
        if separator:
            title = header[:separator.start()].strip(" |,-")
            employer = header[separator.end():].strip(" |,-")
        else:
            title = re.split(r"\s*(?:\||–|—)\s*", header, maxsplit=1)[0].strip()

    non_header_lines = [
        _without_date_ranges(line)
        for line in lines
        if _without_date_ranges(line)
        and _without_date_ranges(line) != header
    ]
    responsibilities = [
        re.sub(r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s*", "", line)
        for line in non_header_lines
    ]
    tools_by_normalized_name = {
        tool.casefold(): tool
        for tool in (
            [match.group(0) for match in _EMPLOYMENT_TOOL_RE.finditer(source_text)]
            + extract_skills(source_text)
        )
    }
    tools = sorted(tools_by_normalized_name.values(), key=str.casefold)
    is_internship = bool(re.search(r"\bintern(?:ship)?\b", title or "", re.IGNORECASE))
    confidence = "high" if confident_header and title else "ambiguous"
    return {
        "title": title,
        "employer": employer,
        "startDateEvidence": date_evidence["startDate"],
        "endDateEvidence": date_evidence["endDate"],
        "isCurrent": date_evidence["current"],
        "responsibilities": responsibilities,
        "technologiesAndTools": tools,
        "sourceText": source_text,
        "isInternship": is_internship if title else None,
        "extractionConfidence": confidence,
        "evidenceStatus": (
            "structured" if confidence == "high" else "ambiguous"
        ),
        "dateEvidence": date_evidence,
    }


def _employment_evidence(lines: list[str]) -> list[dict[str, Any]]:
    if not any(line.strip() for line in lines):
        return []

    records: list[dict[str, Any]] = []
    current: list[str] = []
    current_is_header = False

    def flush() -> None:
        nonlocal current, current_is_header
        if current:
            records.append(_employment_record(current, current_is_header))
            current = []
            current_is_header = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        text = _BULLET_PREFIX.sub("", stripped)
        is_header = _employment_header(text)
        date_only = bool(_dated_range_months(text)[0]) and not _EMPLOYMENT_TITLE_RE.search(text)
        if is_header and current:
            flush()
        elif date_only and current and not _dated_range_months("\n".join(current))[0]:
            current.append(text)
            continue
        elif date_only and current and _dated_range_months("\n".join(current))[0]:
            flush()
        current.append(text)
        if is_header:
            current_is_header = True
    flush()

    return records


def _project_blocks(lines: list[str]) -> list[dict[str, str]]:
    blocks: list[str] = []
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            block = _normalize_whitespace(" ".join(current_lines))
            if block:
                blocks.append(block)
            current_lines.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        is_bullet = bool(_BULLET_PREFIX.match(stripped))
        is_date = bool(_DATE_PREFIX.match(stripped))
        is_title = bool(_PROJECT_TITLE_LINE.match(stripped))
        if current_lines and (is_bullet or is_date or is_title):
            flush()
        cleaned = _BULLET_PREFIX.sub("", stripped)
        if cleaned:
            current_lines.append(cleaned)

    flush()
    return [{"text": block} for block in blocks]


def _education_fallback_start(line: str) -> int | None:
    strong_match = _STRONG_EDUCATION_EVIDENCE.search(line)
    if strong_match:
        if _EXPERIENCE_EVIDENCE.search(line) or _PROJECT_LANGUAGE.search(line):
            return None
        return strong_match.start()
    return None


def _split_education_fallback(
    section_lines: dict[str, list[str]],
    unassigned_lines: list[str],
) -> list[str]:
    education_lines = list(section_lines["education"])
    for line in list(unassigned_lines):
        education_start = _education_fallback_start(line)
        if education_start is None:
            continue

        prefix = line[:education_start].strip()
        education_part = line[education_start:].strip()
        if prefix:
            unassigned_lines.append(prefix)
        if education_part:
            education_lines.append(education_part)
        unassigned_lines.remove(line)

    section_lines["education"] = education_lines
    return education_lines


def _split_experience_fallback(
    section_lines: dict[str, list[str]],
    unassigned_lines: list[str],
) -> None:
    if section_lines["experience"]:
        return

    experience_lines: list[str] = []
    for line in list(unassigned_lines):
        has_dataset_title = any(pattern.search(line) for pattern in _DATASET_EXPERIENCE_PATTERNS)
        has_experience_evidence = (
            bool(_EXPERIENCE_EVIDENCE.search(line)) or has_dataset_title
        )
        has_employment_context = bool(
            re.search(
                r"\b(?:at\s+[A-Z][\w&.'-]+|company|employer|employment|"
                r"work\s+history|worked\s+at|working\s+at)\b",
                line,
            )
        )
        if not has_experience_evidence:
            continue
        if not has_employment_context:
            continue

        experience_lines.append(line)
        unassigned_lines.remove(line)

    section_lines["experience"] = experience_lines


def extract_structured_information(
    text: str,
    include_employment_evidence: bool = True,
) -> dict[str, Any]:
    section_lines: dict[str, list[str]] = {
        "experience": [],
        "education": [],
        "projects": [],
    }
    active_section: str | None = None
    unassigned_lines: list[str] = []

    for original_line in text.splitlines():
        line = _split_camel_case_boundaries(original_line)
        matches = [
            (match, section)
            for match, section in _line_heading_matches(line)
            if _is_embedded_heading(line, match, section)
        ]
        if not matches:
            if active_section:
                section_lines[active_section].append(line)
            elif line.strip():
                unassigned_lines.append(line)
            continue

        cursor = 0
        for match, section in matches:
            content = line[cursor : match.start()].strip()
            if content:
                if active_section:
                    section_lines[active_section].append(content)
                else:
                    unassigned_lines.append(content)
            active_section = section if section in section_lines else None
            cursor = match.end()

            remainder = line[cursor:]
            if remainder.lstrip().startswith(":"):
                remainder = remainder.lstrip()[1:]
                cursor = len(line) - len(remainder)
        trailing = line[cursor:].strip()
        if trailing:
            if active_section:
                section_lines[active_section].append(trailing)
            else:
                unassigned_lines.append(trailing)

    _split_education_fallback(section_lines, unassigned_lines)
    _split_experience_fallback(section_lines, unassigned_lines)

    structured: dict[str, Any] = {
        "skills": extract_skills(text),
        "experience": _section_blocks(section_lines["experience"]),
        "education": _section_blocks(section_lines["education"]),
        "projects": _project_blocks(section_lines["projects"]),
    }
    if include_employment_evidence:
        structured["employmentEvidence"] = _employment_evidence(
            section_lines["experience"]
        )
    return structured