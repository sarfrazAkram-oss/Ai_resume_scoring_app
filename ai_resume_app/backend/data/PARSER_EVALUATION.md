# Parser Coverage Evaluation

Evaluation date: 2026-10-02.

Source: `archive (2).zip`, `Resume/Resume.csv`, stratified by the 24 `Category` values. Three records per category were selected deterministically, producing 72 text records. A matching PDF was evaluated for each selected ID, also 72 PDFs. This is extraction coverage, not accuracy: the dataset does not provide ground-truth section labels.

## Results

| Input | Tested | Parse failures | Skills non-empty | Experience non-empty | Education non-empty | Projects non-empty |
|---|---:|---:|---:|---:|---:|---:|
| `Resume_str` | 72 | 0 | 72 / 72 (100.00%) | 71 / 72 (98.61%) | 67 / 72 (93.06%) | 0 / 72 (0.00%) |
| Matching PDFs | 72 | 0 | 72 / 72 (100.00%) | 72 / 72 (100.00%) | 72 / 72 (100.00%) | 7 / 72 (9.72%) |

## Interpretation

The current parser consistently recovers non-empty skills, experience, and education on this stratified sample. Projects are rarely detected from `Resume_str` but appear in a small PDF subset. That is a coverage signal, not proof of section accuracy: the source does not label the correct section boundaries. PDF extraction/layout differences likely affect heading detection and project coverage.

The evaluation used the existing production extractor for PDFs and the existing structured parser for both text and extracted PDF text. No production parsing code was modified by the evaluation, and no PDFs were permanently extracted.

## Reproduction

From the repository root:

```powershell
C:/Users/HP/AppData/Local/AI_RESUME_BACKEND_VENV/Scripts/python.exe backend/scripts/evaluate_parser.py
```
