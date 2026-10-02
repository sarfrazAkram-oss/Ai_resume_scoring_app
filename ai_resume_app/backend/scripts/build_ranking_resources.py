"""Build compact deterministic vocabulary resources from the relational archive."""

from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_ARCHIVE = ROOT / "data" / "raw" / "archive (3).zip"
OUTPUT_DIR = ROOT / "data" / "processed"
MIN_TERM_FREQUENCY = 3
MAX_TERMS = 5_000


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _usable_term(value: str, *, max_words: int = 8) -> bool:
    term = _clean(value)
    if not term or len(term) > 80 or len(term.split()) > max_words:
        return False
    if sum(character.isalpha() for character in term) < 2:
        return False
    if re.search(r"[.!?]{2,}|https?://|@", term):
        return False
    if re.search(r"\b(?:the|this|that|with|and|from)\b", term.casefold()) and len(term.split()) > 5:
        return False
    return True


def _count_column(archive: zipfile.ZipFile, member: str, column: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    with archive.open(member, "r") as binary_stream:
        reader = csv.DictReader(
            __import__("io").TextIOWrapper(
                binary_stream, encoding="utf-8-sig", errors="replace", newline=""
            )
        )
        for row in reader:
            value = _clean(row.get(column, "") or "")
            if _usable_term(value):
                counts[value.casefold()] += 1
    return counts


def _canonical_counts(
    archive: zipfile.ZipFile,
    specs: tuple[tuple[str, str], ...],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for member, column in specs:
        counts.update(_count_column(archive, member, column))
    return counts


def _write_terms(filename: str, counts: Counter[str], source: str) -> None:
    terms = [
        {"term": term, "frequency": frequency}
        for term, frequency in counts.most_common()
        if frequency >= MIN_TERM_FREQUENCY
    ][:MAX_TERMS]
    (OUTPUT_DIR / filename).write_text(
        json.dumps(
            {
                "source": source,
                "min_frequency": MIN_TERM_FREQUENCY,
                "term_count": len(terms),
                "terms": terms,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_resources() -> dict[str, int]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RAW_ARCHIVE) as archive:
        skill_counts = _canonical_counts(
            archive,
            (
                ("02_abilities.csv", "ability"),
                ("05_person_skills.csv", "skill"),
                ("06_skills.csv", "skill"),
            ),
        )
        education_counts = _count_column(archive, "03_education.csv", "program")
        experience_counts = _count_column(archive, "04_experience.csv", "title")

    _write_terms("skills_vocabulary.json", skill_counts, "archive (3).zip skill/ability tables")
    _write_terms("education_vocabulary.json", education_counts, "archive (3).zip education.program")
    _write_terms("experience_vocabulary.json", experience_counts, "archive (3).zip experience.title")
    return {
        "skills": sum(1 for value in skill_counts.values() if value >= MIN_TERM_FREQUENCY),
        "education": sum(1 for value in education_counts.values() if value >= MIN_TERM_FREQUENCY),
        "experience": sum(1 for value in experience_counts.values() if value >= MIN_TERM_FREQUENCY),
    }


if __name__ == "__main__":
    print(json.dumps(build_resources(), indent=2))