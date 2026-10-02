"""Evaluate structured extraction coverage on a stratified resume sample."""

from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ARCHIVE = ROOT / "data" / "raw" / "archive (2).zip"
SAMPLE_PER_CATEGORY = 3

from app.services.resume_structurer import extract_structured_information


def _text_coverage(text: str) -> dict[str, bool]:
    structured = extract_structured_information(text)
    return {
        "skills": bool(structured["skills"]),
        "experience": bool(structured["experience"]),
        "education": bool(structured["education"]),
        "projects": bool(structured["projects"]),
    }


def _sample_resume_rows() -> list[dict[str, str]]:
    with zipfile.ZipFile(ARCHIVE) as archive:
        with archive.open("Resume/Resume.csv", "r") as stream:
            rows = list(csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace", newline="")))
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if len(grouped[row.get("Category", "unknown")]) < SAMPLE_PER_CATEGORY:
            grouped[row.get("Category", "unknown")].append(row)
    return [row for category in sorted(grouped) for row in grouped[category]]


def _sample_pdf_results(rows: list[dict[str, str]]) -> tuple[int, int, dict[str, int]]:
    selected_ids = {row["ID"] for row in rows}
    results: list[dict[str, bool]] = []
    failures = 0
    with zipfile.ZipFile(ARCHIVE) as archive:
        for member in archive.namelist():
            if not member.casefold().endswith(".pdf") or Path(member).stem not in selected_ids:
                continue
            try:
                with archive.open(member, "r") as stream:
                    text = "\n".join(page.extract_text() or "" for page in PdfReader(stream).pages)
                results.append(_text_coverage(text))
            except Exception:
                failures += 1
    return len(results), failures, _coverage_counts(results)


def _coverage_counts(results: list[dict[str, bool]]) -> dict[str, int]:
    return {
        section: sum(1 for result in results if result[section])
        for section in ("skills", "experience", "education", "projects")
    }


def evaluate() -> dict[str, object]:
    rows = _sample_resume_rows()
    text_results = [_text_coverage(row.get("Resume_str", "")) for row in rows]
    pdf_count, pdf_failures, pdf_coverage = _sample_pdf_results(rows)
    return {
        "source": "archive (2).zip / Resume/Resume.csv",
        "sample_per_category": SAMPLE_PER_CATEGORY,
        "categories_tested": len({row.get("Category", "unknown") for row in rows}),
        "text_records_tested": len(text_results),
        "text_parse_failures": sum(1 for row in rows if not row.get("Resume_str", "").strip()),
        "text_nonempty_sections": _coverage_counts(text_results),
        "text_section_rates_percent": {
            section: round(count / len(text_results) * 100, 2) if text_results else 0.0
            for section, count in _coverage_counts(text_results).items()
        },
        "pdf_records_tested": pdf_count,
        "pdf_parse_failures": pdf_failures,
        "pdf_nonempty_sections": pdf_coverage,
        "pdf_section_rates_percent": {
            section: round(count / pdf_count * 100, 2) if pdf_count else 0.0
            for section, count in pdf_coverage.items()
        },
        "ground_truth_available": False,
        "interpretation": "coverage evaluation only; non-empty sections are not accuracy labels",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))