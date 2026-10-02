# Dataset Analysis

Inspection date: 2026-10-02. The five top-level raw inputs were inspected without extracting archives or changing their contents. CSV inspection used streaming reads; large-table duplicate/key tracking was bounded and marked when capped. No model was trained.

## 1. Dataset Inventory

| Top-level file | Type | Contents / records |
|---|---|---|
| `archive (1).zip` | ZIP | `ai_resume_screening.csv`, 30,000 rows, 7 columns |
| `archive (2).zip` | ZIP | `Resume/Resume.csv`, 2,484 rows, 4 columns; 2,484 PDFs in 24 job-category folders |
| `archive (3).zip` | ZIP | Six relational CSVs: people, abilities, education, experience, person skills, skill vocabulary |
| `archive.zip` | ZIP | `resume_screening_automation.csv`, 100 rows, 3 columns |
| `resume_screening_automation.csv` | CSV | 100 rows, 3 columns; byte-normalized duplicate of the CSV inside `archive.zip` |

## 2. Dataset Structures

### `archive (1).zip` / `ai_resume_screening.csv`

Columns and observed types:

- `years_experience`: integer-like; 16 unique values; no nulls.
- `skills_match_score`: numeric-like; 795 unique values; range 0.5 to 100.0; mean 73.683; no nulls.
- `education_level`: text; `Bachelors` 13,461, `Masters` 10,524, `PhD` 3,024, `High School` 2,991.
- `project_count`: integer-like; 26 unique values; no nulls.
- `resume_length`: integer-like; 751 unique values; no nulls.
- `github_activity`: integer-like; 786 unique values; no nulls.
- `shortlisted`: text target with `Yes` 20,966 and `No` 9,034; no nulls.

The file has no raw resume text, job title, job description, or job requirements. It is structured screening data rather than candidate/job pairs.

### `archive (2).zip` / `Resume/Resume.csv`

Columns:

- `ID`: integer-like identifier, 2,484 unique values, no nulls.
- `Resume_str`: text resume content, one null.
- `Resume_html`: HTML resume content, no nulls.
- `Category`: text category, 24 categories, no nulls.

The archive also contains exactly 2,484 PDFs under `data/data/<CATEGORY>/<ID>.pdf`. PDF category counts include `INFORMATION-TECHNOLOGY` 120, `BUSINESS-DEVELOPMENT` 120, `ADVOCATE` 118, `ENGINEERING` 118, `ACCOUNTANT` 118, and the remaining categories from 22 to 118 records. PDF ID stems match all 2,484 CSV `ID` values: 100% CSV-to-PDF and 100% PDF-to-CSV coverage.

Representative rows contain IDs and categories such as `HR`; their resume text/HTML fields are populated long-form text. Full personal/resume contents were not copied into this report.

### `archive (3).zip`

All six tables use `person_id` as the join key where present:

| CSV | Rows | Columns | Nulls / duplicate rows |
|---|---:|---|---|
| `01_people.csv` | 54,933 | `person_id`, `name`, `email`, `phone`, `linkedin` | name 114; email 53,346; phone 53,106; linkedin 46,401 nulls; 0 duplicate rows |
| `02_abilities.csv` | 1,219,473 | `person_id`, `ability` | no nulls; exact duplicate count capped because table exceeded the bounded hash limit; 54,930 distinct people |
| `03_education.csv` | 75,999 | `person_id`, `institution`, `program`, `start_date`, `location` | institution 1,569; program 7,761; start_date 21,132; location 23,259 nulls; 51 duplicate rows |
| `04_experience.csv` | 265,404 | `person_id`, `title`, `firm`, `start_date`, `end_date`, `location` | title 111; firm 4,206; start_date 2,268; end_date 2,730; location 53,058 nulls; 51 duplicate rows |
| `05_person_skills.csv` | 2,483,376 | `person_id`, `skill` | skill 9 nulls; exact duplicate count capped; 54,858 distinct people |
| `06_skills.csv` | 226,760 | `skill` | 2 nulls; 0 duplicate rows; 226,760 non-empty unique values in the scan |

Examples show real relational content: person 1 has database-administration abilities, a Lead City University Bachelor of Science record, multiple database administrator jobs, and skills such as Database administration and Ms sql server.

### `archive.zip` and standalone CSV

Both contain the same three columns: `resume_text`, `job_title`, `suitability_score`. Both have 100 rows, no nulls, 0 exact duplicate rows, five job titles, and score range 0.03 to 1.0 with mean 0.584. The two CSV contents matched exactly after normalized CSV reading; they are one dataset, not two training sources.

## 3. Duplicate Dataset Findings

- `resume_screening_automation.csv` is an exact duplicate of `archive.zip:resume_screening_automation.csv`.
- `archive (1).zip` is not a duplicate of the 100-row screening CSV; it contains the separate 30,000-row structured screening dataset.
- `archive (2).zip` and `archive (3).zip` have different schemas and purposes.
- The relational education and experience tables each contain 51 exact duplicate rows.
- Large `02_abilities.csv` and `05_person_skills.csv` duplicate counts were intentionally not declared exact because the bounded analyzer capped row-hash tracking for safety.

## 4. Dataset Quality

- The 30K screening data is complete for its seven columns, but has no resume text or job requirements and appears feature-engineered.
- The resume/PDF archive has only one missing `Resume_str`, while `Resume_html` is complete; its category labels are useful for stratified parser tests but are not job-fit labels.
- The relational archive is broad but sparse in contact fields and has missing education/experience attributes. It has strong scale for vocabulary normalization and terminology analysis, but no explicit matching target.
- The 100-row suitability data is complete and small. Its resume text is short synthetic-style feature language such as `Experienced in machine learning, data analysis, statistics.` rather than linked recruiter requirements.

## 5. Useful Columns

- Parser testing: `Resume_str`, `Resume_html`, `ID`, `Category`, and matching PDF filenames in `archive (2).zip`.
- Skills vocabulary: `ability`, `skill`, `02_abilities.csv`, `05_person_skills.csv`, and `06_skills.csv`.
- Education normalization: `program`, `institution`, `start_date` in `03_education.csv`.
- Experience normalization: `title`, `firm`, `start_date`, `end_date` in `04_experience.csv`; `years_experience` in the 30K screening data is a compact feature but not raw evidence.
- Job-title vocabulary: `name` in `01_people.csv` and `title` in `04_experience.csv`; these are person/job-history labels, not recruiter job postings.
- Target-like labels: `shortlisted`, `suitability_score`, and `skills_match_score`.

## 6. Target/Label Analysis

The 30K dataset has a binary `shortlisted` target with a 69.887% positive rate. It has no job title, requirement text, or resume text. The 100-row dataset has continuous `suitability_score` but only five job titles and no job requirements or explicit shortlist outcome.

The resume/PDF archive's `Category` is a resume/job-category label, not evidence that a candidate was suitable for a particular recruiter job. The relational archive has no obvious suitability/ranking/shortlist label.

## 7. Leakage Risks

`skills_match_score` is a direct match-like feature and is very likely close to one of the current ranking components. It must not be used as an input while evaluating a target that is shortlist-like without a carefully defined causal boundary. In this dataset, shortlisted candidates have average `skills_match_score` 79.288 versus 60.673 for non-shortlisted candidates, so it is strongly target-associated and may encode the decision itself.

Other 30K fields such as `project_count`, `github_activity`, and `resume_length` may be useful auxiliary predictors, but they are already engineered and have no link to a concrete job requirement. `education_level` is coarse and `years_experience` is already summarized. Treat this dataset as a screening-policy analysis/validation source, not proof that the current four-component scorer is correct.

The 100-row `suitability_score` is itself an outcome label. Resume text contains skill-like phrases, but there are no requirements, so using it to train job-specific matching would encourage title-to-score shortcuts. It is also duplicated between two files.

## 8. Usefulness for Skills

Best source: `archive (3).zip`, especially `06_skills.csv` and the `skill` columns in `05_person_skills.csv` and `02_abilities.csv`. It provides a large vocabulary and person-linked frequency counts. It contains noisy phrases and many non-technical abilities, so it needs normalization, deduplication, and category review before replacing the current explicit skill vocabulary.

The 30K `skills_match_score` is not suitable for building a vocabulary; it is a precomputed score and leakage risk. The 100-row text can provide small examples only.

## 9. Usefulness for Experience

Best source: `04_experience.csv`, with 265,404 records linked to 54,933 people through `person_id`. Titles, firms, start dates, and end dates can validate duration parsing and terminology. Missing dates and 53,058 missing locations require cleaning. The 30K `years_experience` can validate numeric boundary cases but is an engineered feature, not raw evidence.

## 10. Usefulness for Education

Best source: `03_education.csv`, with 75,999 person-linked records and real `program`/`institution` text. It can expand degree and institution normalization, but program labels are noisy and 7,761 program values are null. It has no job-required education or suitability label.

## 11. Usefulness for Projects

No dataset has a reliable structured project field connected to a job requirement. `Resume_str`/`Resume_html` may contain project sections for parser testing, but they have no project relevance labels. `project_count` in the 30K dataset is only a numeric feature and cannot validate project-to-job relevance by itself.

## 12. Usefulness for Resume Parsing

Best source: `archive (2).zip`. It has 2,484 text/HTML resume records and 2,484 matching PDFs across 24 categories. It can test the current PDF extractor and structured section parser on a small, linked, multi-domain sample. Do not run every PDF automatically yet; begin with a stratified sample and compare extracted text against `Resume_str`.

The 100-row dataset contains text but no PDFs and is too small for broad parser validation.

## 13. Suitability for ML Training

- `archive (2).zip`: not suitable as supervised job-resume matching training because it has resume/category labels but no recruiter job requirements or suitability outcomes. Suitable for parser evaluation and category-stratified text experiments.
- `archive (3).zip`: not suitable as supervised ranking training because it has no match/shortlist target and no job-posting side. Suitable for vocabulary, aliases, education normalization, and experience terminology.
- `archive (1).zip`: not suitable for primary matching-model training because it lacks resume text, job title, job requirements, and job-resume pairs; `skills_match_score` is precomputed and leakage-prone. It can support screening-label diagnostics only.
- `archive.zip` plus standalone CSV: not suitable for primary training; only 100 duplicated rows, five job titles, no requirements, and a pre-existing suitability label.

No supplied dataset currently contains clean `(resume, recruiter job requirements, outcome)` triples suitable for primary supervised training.

## 14. Recommended Dataset(s)

1. Use `archive (2).zip` for staged PDF/text extractor and structured-parser validation, with `ID` to PDF-stem matching.
2. Use `archive (3).zip` to expand skills, education, degree, job-title, and experience vocabularies through `person_id` joins and chunked aggregation.
3. Use a deduplicated, leakage-audited slice of `archive (1).zip` only for secondary screening-policy validation; exclude `skills_match_score` from any model that evaluates shortlist-like outcomes.

## 15. Datasets Not Recommended for Primary Training

Do not use the duplicated 100-row suitability CSV as primary training data. Do not use the 30K screening CSV as job-specific ranking training. Do not treat resume categories in the PDF archive as suitability labels. Do not count the standalone 100-row CSV and its ZIP copy as separate data.

## 16. Recommended Next Step

This phase completed the first focused dataset enhancement: `backend/scripts/build_ranking_resources.py` generated compact resources from `archive (3).zip` containing 5,000 filtered skill terms, 5,000 education-program terms, and 5,000 experience-title terms. The resources are optional at runtime: manual mappings remain authoritative, exact boundary matching remains required, and a missing resource falls back to the existing deterministic behavior. Dataset skills extend structured resume recognition; education terms only surface unknown vocabulary without assigning level/field; experience titles support section recognition but never create years.

The parser coverage harness in `backend/scripts/evaluate_parser.py` then evaluated 72 text resumes and 72 matching PDFs from all 24 categories. Results are recorded in `backend/data/PARSER_EVALUATION.md`. The next engineering step should be a small parser-quality review of the low project-section coverage, not ML training.

One defensible later ML experiment would be a leakage-controlled comparison on `archive (1).zip`: reserve `shortlisted` as the target, split by a fixed seed, exclude `skills_match_score` and any other precomputed match-like fields, and report stratified accuracy, precision, recall, F1, ROC-AUC, and a confusion matrix. This would be a screening-policy experiment only, not the production recruiter-job ranking model, because the dataset has no resume/job-requirement pairs.

## Safety And Reproducibility

`backend/scripts/analyze_datasets.py` performs streaming CSV and ZIP inspection, does not extract archives permanently, and uses a bounded in-memory/temporary analysis strategy for large tables. The raw five files were not modified. `.gitignore` now excludes `backend/data/raw/`, generated data directories, and future model artifacts while leaving this report trackable. No model files, model training, Firebase/Supabase access, or ranking-code changes were made.
