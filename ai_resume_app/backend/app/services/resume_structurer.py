import re

from app.services.dataset_resources import load_terms


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
        "UNIVERSITY PROJECTS",
        "PROJECT EXPERIENCE",
        "PROJECTS & EXPERIENCE",
    ),
    "skills": (
        "SKILLS",
        "TECHNICAL SKILLS",
        "CORE SKILLS",
        "TECHNOLOGIES",
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
_EDUCATION_EVIDENCE = re.compile(
    r"\b(?:bachelor(?:'s)?|bs(?:cs|se)?|bsc|master(?:'s)?|ms(?:cs|se)?|msc|"
    r"matric|fsc|intermediate|degree|(?:\d+(?:st|nd|rd|th)\s+)?semester|"
    r"university|college)\b",
    re.IGNORECASE,
)
_STRONG_EDUCATION_EVIDENCE = re.compile(
    r"\b(?:bachelor(?:'s)?|bs(?:cs|se)?|bsc|master(?:'s)?|ms(?:cs|se)?|msc|"
    r"matric|fsc|intermediate|degree|(?:\d+(?:st|nd|rd|th)\s+)?semester)\b",
    re.IGNORECASE,
)
_EXPERIENCE_EVIDENCE = re.compile(
    r"\b(?:intern(?:ship)?s?|software\s+engineer|developer|engineer|employment|"
    r"experience|company|\d+\s*\+?\s*(?:months?|years?))\b",
    re.IGNORECASE,
)
_EXPERIENCE_CONTEXT = re.compile(
    r"\b(?:at\s+[A-Z][\w&.'-]+|company|employment|\d+\s*\+?\s*"
    r"(?:months?|years?)|\d{4}\s*(?:-|–|—|to)\s*(?:\d{4}|present|current))\b",
    re.IGNORECASE,
)
_PROJECT_LANGUAGE = re.compile(
    r"\b(?:project|built|developed|created|designed|implemented|implemented|"
    r"application|prototype|team\s+leader)\b",
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


def extract_skills(text: str) -> list[str]:
    found: list[tuple[int, str]] = []
    for canonical, pattern in _SKILL_PATTERNS:
        match = pattern.search(text)
        if match:
            found.append((match.start(), canonical))
    for canonical, pattern in _DATASET_SKILL_PATTERNS:
        match = pattern.search(text)
        if match:
            found.append((match.start(), canonical))

    skills: list[str] = []
    seen: set[str] = set()
    for _, canonical in sorted(found, key=lambda item: (item[0], item[1].casefold())):
        normalized = canonical.casefold()
        if normalized not in seen:
            seen.add(normalized)
            skills.append(canonical)
    return skills


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


def _education_fallback_start(line: str) -> int | None:
    strong_match = _STRONG_EDUCATION_EVIDENCE.search(line)
    if strong_match:
        if _EXPERIENCE_EVIDENCE.search(line):
            return 0
        return strong_match.start()

    if _EDUCATION_EVIDENCE.search(line) and not _PROJECT_LANGUAGE.search(line):
        return 0
    return None


def _split_education_fallback(
    section_lines: dict[str, list[str]],
    unassigned_lines: list[str],
) -> list[str]:
    education_lines = list(section_lines["education"])
    all_sources = [
        (section, line)
        for section, lines in section_lines.items()
        if section != "education"
        for line in lines
    ] + [(None, line) for line in unassigned_lines]

    for section, line in all_sources:
        education_start = _education_fallback_start(line)
        if education_start is None:
            continue

        prefix = line[:education_start].strip()
        education_part = line[education_start:].strip()
        if prefix:
            if section is None:
                unassigned_lines.append(prefix)
            else:
                section_lines[section].append(prefix)
        if education_part:
            education_lines.append(education_part)
        if section is None:
            unassigned_lines.remove(line)
        else:
            section_lines[section].remove(line)

    section_lines["education"] = education_lines
    return education_lines


def _split_experience_fallback(
    section_lines: dict[str, list[str]],
    unassigned_lines: list[str],
) -> None:
    if section_lines["experience"]:
        return

    experience_lines: list[str] = []
    sources = [
        ("projects", line)
        for line in section_lines["projects"]
    ] + [(None, line) for line in unassigned_lines]
    for section, line in sources:
        has_dataset_title = any(pattern.search(line) for pattern in _DATASET_EXPERIENCE_PATTERNS)
        has_experience_evidence = bool(_EXPERIENCE_EVIDENCE.search(line)) or has_dataset_title
        has_employment_context = bool(_EXPERIENCE_CONTEXT.search(line))
        if not has_experience_evidence:
            continue
        if section == "projects" and not has_employment_context:
            continue

        experience_lines.append(line)
        if section is None:
            unassigned_lines.remove(line)
        else:
            section_lines[section].remove(line)

    section_lines["experience"] = experience_lines


def extract_structured_information(text: str) -> dict[str, list[str] | list[dict[str, str]]]:
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

    return {
        "skills": extract_skills(text),
        "experience": _section_blocks(section_lines["experience"]),
        "education": _section_blocks(section_lines["education"]),
        "projects": _section_blocks(section_lines["projects"]),
    }