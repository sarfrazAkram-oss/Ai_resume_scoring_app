"""Stream dataset metadata and quality summaries without extracting archives."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
import tempfile
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CHUNK_ROWS = 20_000
SAMPLE_ROWS = 3
SAMPLE_CELL_LIMIT = 220
TYPE_SAMPLE_ROWS = 2_000
MAX_EXACT_ROW_HASHES = 300_000
MAX_KEY_VALUES = 100_000


def _is_null(value: str | None) -> bool:
    return value is None or not value.strip() or value.strip().casefold() in {
        "na",
        "n/a",
        "nan",
        "null",
        "none",
    }


def _cell_type(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        return "empty"
    try:
        int(candidate)
        return "integer"
    except ValueError:
        pass
    try:
        float(candidate)
        return "number"
    except ValueError:
        pass
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        try:
            date.fromisoformat(candidate)
            return "date"
        except ValueError:
            pass
    return "text"


def _truncate(value: str, limit: int = SAMPLE_CELL_LIMIT) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    return compact if len(compact) <= limit else compact[:limit] + "..."


def _dataset_description(name: str, headers: list[str], samples: list[dict[str, str]]) -> dict[str, Any]:
    lower_names = {header.casefold() for header in headers}
    joined_headers = " ".join(lower_names)
    sample_text = " ".join(
        value.casefold()
        for row in samples
        for value in row.values()
        if value
    )
    return {
        "has_resume_text": any(
            re.search(r"resume.*(?:text|content)|(?:text|content).*resume", header.casefold())
            for header in headers
        ),
        "has_resume_pdf_paths": any(".pdf" in value.casefold() for value in sample_text.split()),
        "has_skills": any("skill" in header.casefold() or "ability" in header.casefold() for header in headers),
        "has_experience": any("experience" in header.casefold() or "year" in header.casefold() for header in headers),
        "has_education": any("education" in header.casefold() or "degree" in header.casefold() for header in headers),
        "has_job_title": any("job_title" in header.casefold() or "job title" in header.casefold() for header in headers),
        "has_job_requirements": any(
            any(term in header.casefold() for term in ("required_skill", "job_description", "job_requirement", "job_text"))
            for header in headers
        ),
        "label_columns": [
            header for header in headers
            if any(term in header.casefold() for term in ("label", "score", "shortlist", "selected", "suitability", "ranking", "target"))
        ],
        "sample_resume_mentions_pdf": ".pdf" in sample_text,
        "sample_mentions_experience_terms": bool(re.search(r"\b(years?|months?|experience)\b", sample_text)),
        "sample_mentions_education_terms": bool(re.search(r"\b(bachelor|master|degree|university|education|matric|fsc)\b", sample_text)),
        "sample_has_project_terms": bool(re.search(r"\b(projects?|portfolio)\b", sample_text)),
        "header_count": len(headers),
        "name": name,
    }


def _open_csv(path: Path) -> TextIO:
    return path.open("r", encoding="utf-8-sig", errors="replace", newline="")


def _summarize_csv(
    source_name: str,
    stream: TextIO,
    sqlite_connection: sqlite3.Connection,
) -> dict[str, Any]:
    reader = csv.DictReader(stream)
    headers = [str(header) for header in (reader.fieldnames or [])]
    if not headers:
        return {"source": source_name, "error": "CSV has no header row."}

    row_count = 0
    null_counts = Counter({header: 0 for header in headers})
    type_counts: dict[str, Counter[str]] = {header: Counter() for header in headers}
    samples: list[dict[str, str]] = []
    bounded_counts: dict[str, Counter[str] | None] = {}
    distinct_estimates: dict[str, set[str] | None] = {}
    likely_key_columns = [
        header for header in headers
        if re.search(r"(?:^|[_\s])(id|person_id|resume_id|candidate_id|skill_id|job_id)$", header.casefold())
    ]
    for header in headers:
        if any(token in header.casefold() for token in ("label", "score", "status", "category", "class", "title", "skill", "education", "degree")):
            bounded_counts[header] = Counter()
            distinct_estimates[header] = set()

    row_digests: set[str] | None = set()
    key_values: dict[str, set[str] | None] = {
        header: set() for header in likely_key_columns
    }
    type_rows_seen = 0

    for row in reader:
        row_count += 1
        values = {header: row.get(header) or "" for header in headers}
        if len(samples) < SAMPLE_ROWS:
            samples.append({
                key: (
                    f"<redacted text sample; {len(value)} characters>"
                    if any(token in key.casefold() for token in ("resume_text", "resume_content", "resume_html"))
                    else _truncate(value)
                )
                for key, value in values.items()
            })

        normalized_row = json.dumps(
            [values[header].strip() for header in headers],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(normalized_row.encode("utf-8")).hexdigest()
        if row_digests is not None:
            if len(row_digests) < MAX_EXACT_ROW_HASHES:
                row_digests.add(digest)
            else:
                row_digests = None

        for header, value in values.items():
            if _is_null(value):
                null_counts[header] += 1
            if type_rows_seen < TYPE_SAMPLE_ROWS and value.strip():
                type_counts[header][_cell_type(value)] += 1
            if header in bounded_counts and value.strip():
                counts = bounded_counts[header]
                distinct = distinct_estimates[header]
                if counts is not None and distinct is not None:
                    normalized_value = value.strip()
                    if normalized_value not in distinct and len(distinct) >= 2_000:
                        bounded_counts[header] = None
                        distinct_estimates[header] = None
                    else:
                        distinct.add(normalized_value)
                        counts[normalized_value] += 1
            if header in likely_key_columns and value.strip():
                values_for_key = key_values[header]
                if values_for_key is not None:
                    if len(values_for_key) < MAX_KEY_VALUES:
                        values_for_key.add(value.strip())
                    else:
                        key_values[header] = None

        type_rows_seen += 1

    columns: list[dict[str, Any]] = []
    for header in headers:
        counts = bounded_counts.get(header)
        distinct = distinct_estimates.get(header)
        columns.append({
            "name": header,
            "inferred_types_sample": dict(type_counts[header]),
            "null_count": null_counts[header],
            "null_percent": round(null_counts[header] / row_count * 100, 2) if row_count else 0.0,
            "distinct_count": len(distinct) if distinct is not None else None,
            "distinct_count_capped_at": 2_000 if distinct is None else None,
            "top_values": counts.most_common(20) if counts is not None else [],
        })

    return {
        "source": source_name,
        "file_type": "csv",
        "rows": row_count,
        "columns_count": len(headers),
        "columns": columns,
        "exact_duplicate_rows": (
            row_count - len(row_digests) if row_digests is not None else None
        ),
        "exact_duplicate_rows_complete": row_digests is not None,
        "sample_rows": samples,
        "likely_key_unique_counts": {
            header: len(values)
            for header, values in key_values.items()
            if values is not None
        },
        "likely_key_unique_counts_capped": [
            header for header, values in key_values.items() if values is None
        ],
        "description": _dataset_description(source_name, headers, samples),
    }


def inspect_datasets() -> dict[str, Any]:
    if not RAW_DIR.is_dir():
        raise FileNotFoundError(f"Dataset directory not found: {RAW_DIR}")

    top_level_files = sorted(path for path in RAW_DIR.iterdir() if path.is_file())
    with tempfile.TemporaryDirectory(prefix="resume_dataset_analysis_") as temporary_directory:
        connection = sqlite3.connect(Path(temporary_directory) / "inspection.sqlite3")

        csv_summaries: list[dict[str, Any]] = []
        archives: list[dict[str, Any]] = []
        raw_hashes: dict[str, str] = {}
        standalone_hashes: dict[str, str] = {}
        archive_csv_hashes: dict[str, list[str]] = {}
        archive_pdf_info: list[dict[str, Any]] = []

        for path in top_level_files:
            file_digest = hashlib.sha256()
            with path.open("rb") as raw_stream:
                for block in iter(lambda: raw_stream.read(1024 * 1024), b""):
                    file_digest.update(block)
            raw_hashes[path.name] = file_digest.hexdigest()

            if path.suffix.casefold() == ".csv":
                with _open_csv(path) as stream:
                    summary = _summarize_csv(path.name, stream, connection)
                csv_summaries.append(summary)
                standalone_hashes[path.name] = _canonical_csv_hash(path)
            elif path.suffix.casefold() == ".zip":
                archives.append(_inspect_archive(
                    path,
                    connection,
                    csv_summaries,
                    archive_csv_hashes,
                    archive_pdf_info,
                ))

        duplicate_pairs = _find_duplicate_pairs(standalone_hashes, archive_csv_hashes)
        relationship_summary = _summarize_relations(csv_summaries)
        pdf_summary = _summarize_pdf_links(csv_summaries, archive_pdf_info)
        connection.close()

    return {
        "raw_directory": str(RAW_DIR),
        "top_level_file_count": len(top_level_files),
        "top_level_files": [path.name for path in top_level_files],
        "raw_file_sha256": raw_hashes,
        "archives": archives,
        "csv_datasets": csv_summaries,
        "duplicate_csv_copies": duplicate_pairs,
        "relational_summary": relationship_summary,
        "resume_pdf_summary": pdf_summary,
        "inspection_notes": {
            "archives_extracted": False,
            "large_csv_processing": "streaming via csv.DictReader; no full CSV loaded into memory",
            "duplicate_processing": "row hashes and join keys stored in a temporary SQLite database",
            "raw_files_modified": False,
            "models_trained": False,
        },
    }


def _inspect_archive(
    path: Path,
    connection: sqlite3.Connection,
    summaries: list[dict[str, Any]],
    csv_hashes: dict[str, list[str]],
    pdf_info: list[dict[str, Any]],
) -> dict[str, Any]:
    csv_members: list[dict[str, Any]] = []
    member_type_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    other_member_samples: list[dict[str, Any]] = []
    pdf_samples: list[str] = []
    category_counts: Counter[str] = Counter()
    with zipfile.ZipFile(path) as archive:
        members = [entry for entry in archive.infolist() if not entry.is_dir()]
        for entry in members:
            member_name = entry.filename
            suffix = Path(member_name).suffix.casefold()
            member_type = suffix.lstrip(".") or "unknown"
            member_type_counts[member_type] += 1
            extension_counts[suffix or "[no extension]"] += 1
            if suffix == ".csv":
                with archive.open(entry, "r") as binary_stream:
                    text_stream = io.TextIOWrapper(binary_stream, encoding="utf-8-sig", errors="replace", newline="")
                    summary = _summarize_csv(f"{path.name}:{member_name}", text_stream, connection)
                summaries.append(summary)
                digest = _canonical_zip_csv_hash(archive, entry)
                csv_hashes.setdefault(path.name, []).append(digest)
                csv_members.append({
                    "name": member_name,
                    "uncompressed_bytes": entry.file_size,
                    "rows": summary.get("rows"),
                    "columns_count": summary.get("columns_count"),
                    "columns": [column["name"] for column in summary.get("columns", [])],
                    "exact_duplicate_rows": summary.get("exact_duplicate_rows"),
                })
            elif suffix == ".pdf":
                parts = Path(member_name).parts
                category = parts[-2] if len(parts) >= 2 else "unknown"
                pdf_id = Path(member_name).stem
                category_counts[category] += 1
                pdf_info.append({"archive": path.name, "member": member_name, "id": pdf_id, "category": category})
                if len(pdf_samples) < 8:
                    pdf_samples.append(member_name)
            elif suffix != ".pdf" and len(other_member_samples) < 20:
                other_member_samples.append({"name": member_name, "type": member_type, "uncompressed_bytes": entry.file_size})

    return {
        "filename": path.name,
        "file_type": "zip",
        "member_count": sum(member_type_counts.values()),
        "member_type_counts": dict(sorted(member_type_counts.items())),
        "extension_counts": dict(sorted(extension_counts.items())),
        "csv_members": csv_members,
        "other_member_samples": other_member_samples,
        "pdf_path_samples": pdf_samples,
        "pdf_category_counts": dict(sorted(category_counts.items())),
    }


def _canonical_csv_hash(path: Path) -> str:
    with _open_csv(path) as stream:
        return _hash_csv_stream(stream)


def _canonical_zip_csv_hash(archive: zipfile.ZipFile, entry: zipfile.ZipInfo) -> str:
    with archive.open(entry, "r") as binary_stream:
        stream = io.TextIOWrapper(binary_stream, encoding="utf-8-sig", errors="replace", newline="")
        return _hash_csv_stream(stream)


def _hash_csv_stream(stream: TextIO) -> str:
    digest = hashlib.sha256()
    for row in csv.reader(stream):
        digest.update(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _find_duplicate_pairs(
    standalone_hashes: dict[str, str],
    archive_hashes: dict[str, list[str]],
) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    all_hashes = [
        (name, digest)
        for name, digest in standalone_hashes.items()
    ] + [
        (f"{archive}:{index}", digest)
        for archive, digests in archive_hashes.items()
        for index, digest in enumerate(digests)
    ]
    for index, (left_name, left_digest) in enumerate(all_hashes):
        for right_name, right_digest in all_hashes[index + 1 :]:
            if left_digest == right_digest:
                pairs.append({"first": left_name, "duplicate": right_name, "match": "byte-normalized CSV content SHA-256"})
    return pairs


def _summarize_relations(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys: dict[str, dict[str, int]] = {}
    for summary in summaries:
        source = summary["source"]
        keys[source] = summary.get("likely_key_unique_counts", {})
    relations: list[dict[str, Any]] = []
    for source, unique_counts in keys.items():
        for column, count in unique_counts.items():
            if "person" in column.casefold() or column.casefold() in {"id", "personid"}:
                relations.append({"source": source, "key": column, "distinct_nonempty_values": count})
    return relations


def _summarize_pdf_links(
    summaries: list[dict[str, Any]],
    pdf_info: list[dict[str, Any]],
) -> dict[str, Any]:
    resume_tables = [summary for summary in summaries if "resume.csv" in summary["source"].casefold()]
    table_id_sets: dict[str, set[str]] = {}
    # Re-read just primary-key columns from resume metadata CSVs for PDF path matching.
    for summary in resume_tables:
        source = summary["source"]
        if ":" not in source or summary.get("columns_count", 0) == 0:
            continue
        archive_name, member_name = source.split(":", 1)
        archive_path = RAW_DIR / archive_name
        with zipfile.ZipFile(archive_path) as archive:
            with archive.open(member_name, "r") as binary_stream:
                reader = csv.DictReader(io.TextIOWrapper(binary_stream, encoding="utf-8-sig", errors="replace", newline=""))
                id_column = next((name for name in (reader.fieldnames or []) if name.casefold() in {"id", "resume_id", "resumeid"}), None)
                if id_column:
                    table_id_sets[source] = {row[id_column].strip() for row in reader if row.get(id_column, "").strip()}

    pdf_ids = {entry["id"] for entry in pdf_info}
    links = []
    for source, identifiers in table_id_sets.items():
        matches = identifiers & pdf_ids
        links.append({
            "resume_table": source,
            "csv_unique_ids": len(identifiers),
            "pdf_unique_ids": len(pdf_ids),
            "matched_ids": len(matches),
            "csv_ids_with_pdf_percent": round(len(matches) / len(identifiers) * 100, 2) if identifiers else 0.0,
            "pdf_ids_with_csv_percent": round(len(matches) / len(pdf_ids) * 100, 2) if pdf_ids else 0.0,
        })
    return {
        "pdf_count": len(pdf_info),
        "unique_pdf_ids": len(pdf_ids),
        "categories": dict(sorted(Counter(item["category"] for item in pdf_info).items())),
        "csv_pdf_id_links": links,
        "pdf_sample_paths": [item["member"] for item in pdf_info[:5]],
    }


def main() -> None:
    print(json.dumps(inspect_datasets(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()