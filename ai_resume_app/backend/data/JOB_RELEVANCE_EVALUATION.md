# Job-Relevant Experience Matcher Evaluation

**Evaluation date:** 2026-11-04  
**Matcher:** `relevanceMatcherVersion = 1`  
**Boundary:** Offline evaluation only. The matcher was not changed or activated.

## Dataset inventory and evidence quality

| Local source | Available data | Relevance-evaluation suitability |
|---|---|---|
| `raw/archive (2).zip` | `Resume/Resume.csv` and 2,484 PDF files across 24 categories | Resume text exists, but categories are not job-fit labels. Provenance was not independently verified. |
| `ranking_eval/candidates.csv` | 30 deterministic archive references: five each from ACCOUNTANT, ENGINEERING, HEALTHCARE, HR, INFORMATION-TECHNOLOGY, and SALES | Parsed for employment-evidence availability only. No source job postings or independent judgments are paired with these candidates. |
| `ranking_eval/jobs_template.csv` and `relevance_labels_template.csv` | Header-only templates | No authentic job records or human labels are present. |
| `raw/archive (1).zip` | Structured screening rows, including a shortlist field | No raw resumes, job descriptions, or resume/job pairings; not suitable for this matcher. |
| `raw/archive (3).zip` | Relational person, experience, education, and skill data | Experience rows have title, firm, and dates but no responsibility evidence; the source also contains contact fields and was not used. |
| `PARSER_EVALUATION.md` | Prior parser-coverage sample of 72 text records and 72 PDFs | Coverage only, without role-level ground truth or job-specific labels. |

**Counts:** 30 local resume PDFs were inspected for parser evidence availability; **0 authenticity-verified resume/job pairs** were available for relevance evaluation. Archive provenance could not be established from local materials. The evaluation therefore treats those 30 files as archive samples, not verified genuine resumes. The seven domains are covered by **20 synthetic engineering cases**. Their expected labels are provisional scenario expectations, not human-reviewed labels or ground truth.

The 30-file evidence inventory emitted 592 employment-evidence records: 79 with a title, 538 with responsibilities, 9 with verified dates, 583 with missing dates, 0 with ambiguous dates, and 513 with ambiguous extraction status. These records are parser outputs, not verified separate jobs; the high record count and ambiguity indicate role-boundary fragmentation. Category labels were used only to describe sample composition, never to assign relevance.

No personal contact details or resume text from the archive are included in this report.

## Method

The reproducible runner applies the unchanged isolated matcher to each fixture, records expected and predicted relevance, matched requirements/duties/tools, evidence snippets, explanations, duration, and review status. Synthetic expectations were authored as engineering checks and were not derived from matcher outputs. No confusion matrix, precision, recall, F1, accuracy, or real-world ranking claim is appropriate.

The runner also parses the existing 30-PDF sample and reports aggregate evidence counts only. It does not pair those resumes with invented “real” jobs or treat occupational categories as relevance labels. `Present` dates are evaluated with the fixed as-of date **2026-11-04** for reproducibility.

Reproduce from `backend`:

```powershell
& .\.venv\Scripts\python.exe scripts\evaluate_job_relevance.py
```

## Synthetic case results

“Expected” is a provisional scenario label. “Evidence/result” summarizes observable synthetic input and the matcher output. **19 of 20** provisional expectations agreed; this is engineering-case agreement only, not accuracy.

| Case | Domain / scenario | Expected | Predicted | Evidence and result |
|---|---|---|---|---|
| SYN-01 | Software / IT direct | direct | direct | Flutter application development and code maintenance matched. |
| SYN-02 | Healthcare nursing duties | direct | direct | Patient care and medication administration matched. |
| SYN-03 | Engineering, different title | direct | direct | CAD design and technical drawings supported the role despite a title difference. |
| SYN-04 | Marketing / SEO | direct | direct | SEO campaigns and organic-search duties matched. |
| SYN-05 | Accounting / Finance | direct | direct | Bookkeeping and financial reporting matched. |
| SYN-06 | Human Resources | direct | direct | Recruitment and employee onboarding matched. |
| SYN-07 | Sales, different title and paraphrased duties | direct | insufficient_evidence | “Generate leads / acquire clients” did not match the vocabulary phrases “lead generation / client acquisition.” Review needed. |
| SYN-08 | Transferable project/budget duties | transferable | transferable | Explicit project coordination and budget management were kept separate from direct experience. |
| SYN-09 | Sales role for software job | unrelated | unrelated | Explicit lead-generation and client-acquisition evidence supported a different domain. |
| SYN-10 | Same software title, sales duties | insufficient_evidence | insufficient_evidence | Title matched but duties did not; no direct match was awarded. |
| SYN-11 | Global skill only | unrelated | unrelated | Flutter appeared only in global skills; sales employment evidence did not match it. |
| SYN-12 | Title/tool but no responsibilities | insufficient_evidence | insufficient_evidence | Flutter title/tool evidence without employment duties was insufficient for direct relevance. |
| SYN-13 | Relevant duties, ambiguous extraction | direct | direct | Duties supported relevance; ambiguous extraction left duration for review. |
| SYN-14 | Relevant duties, missing dates and “2 years” claim | direct | direct | Relevance matched; undated duration contributed **0** verified months and required review. |
| SYN-15 | Relevant duties, multiple date ranges | direct | direct | Relevance matched; ambiguous dates contributed **0** verified months and required review. |
| SYN-16 | Current employment | direct | direct | Jan 2022–Present produced 58 supported months as of the fixed evaluation date. |
| SYN-17 | Internship | direct | direct | Relevant Jan 2022–Jan 2023 internship produced 12 supported months; no discount was applied. |
| SYN-18 | Multiple non-overlapping roles | direct | direct | Relevant roles aggregated to 36 months. |
| SYN-19 | Overlapping relevant roles | direct | direct | 2020–2022 and 2021–2023 merged to 36 months, not 48. |
| SYN-20 | Concurrent direct and unrelated roles | direct | direct | Engineering received 24 direct months; concurrent unrelated sales time added no direct or transferable months. |

### Domain coverage

| Domain | Synthetic cases | Provisional outcomes |
|---|---:|---|
| Software / IT | 12 | 8 direct, 2 unrelated, 2 insufficient-evidence; all 12 expectations agreed. |
| Healthcare | 1 | Direct; expectation agreed. |
| Engineering | 2 | Both direct; expectations agreed, including the different-title case. |
| Marketing | 1 | Direct; expectation agreed. |
| Accounting / Finance | 1 | Direct; expectation agreed. |
| Human Resources | 1 | Direct; expectation agreed. |
| Sales | 1 | Expected direct, predicted insufficient evidence; expectation disagreed. |
| Cross-domain transferable | 1 | Transferable; expectation agreed. |

The archive-backed sample does not include marketing candidates. No performance by domain can be inferred from these synthetic cases or from archive category labels.

## Duration, review, and error analysis

All **16 explicit duration/review checks passed**:

- Multiple non-overlapping and overlapping relevant roles aggregate to 36 months; overlaps are not double-counted.
- Current employment is bounded by the fixed evaluation date; internship evidence is retained as dated work.
- Missing dates, ambiguous ranges, and undated duration claims yield no verified months and are review-needed.
- Transferable months remain separate (24 in the synthetic transferable case); concurrent direct evidence takes priority over overlapping unrelated/transferable time.

The only synthetic expectation mismatch is **SYN-07**. The matcher uses phrase matching and misses common inflection/paraphrase pairs (“generate leads” vs. “lead generation”; “acquire clients” vs. “client acquisition”). This is a missed relevant match in the fixture, not evidence of a measured real-world false-negative rate. A focused future change should add reviewed phrase variants or controlled normalization and regression cases rather than broadly loosening match thresholds.

The archive sample exposes a larger extraction risk: only 79 of 592 emitted records had titles, and 513 had ambiguous extraction status. Blank lines and layout boundaries can split a single job into multiple records or detach duties/dates from a title. The 583 records without dates cannot establish verified duration. Before relying on real resumes, improve and independently validate role-boundary/date association while preserving source text and uncertainty.

Same-title evidence with unrelated duties (SYN-10) remains insufficient rather than direct; title/tool-only evidence (SYN-12) is also insufficient. These require review, not negative qualification judgments. The synthetic set contains no observed false direct result, but there are no independent labels or authentic job pairs with which to estimate false-direct risk.

## Metrics, limitations, and recommendation

- **Human-reviewed ground truth:** none.
- **Real resume/job relevance pairs:** 0.
- **Synthetic engineering cases:** 20; 19 provisional expectation agreements and 1 disagreement.
- **Accuracy metrics:** not calculated.
- **Data limits:** source provenance is unverified; available job and label templates are blank; archive categories do not establish relevance.
- **Matcher limits:** curated vocabulary misses paraphrases and domain-specific terminology; title/responsibility extraction is fragile; year-only date ranges have year-level rather than month-level precision.
- **Scoring boundary:** this evaluation did not modify matcher rules, live scoring, weights, response keys, stored scores, ranking, Firebase, Supabase, or Flutter.

**Recommendation: insufficient evidence for Phase 6D integration.** Before controlled integration, (1) improve role segmentation and title/date/responsibility association and measure it on permissioned resumes, (2) address narrowly tested paraphrase/inflection misses such as SYN-07, (3) obtain authentic job descriptions and independent reviewer labels across all supported domains, including adjudication, and (4) report held-out per-class metrics and review rates. Transferable experience also needs an explicit scoring policy. Do not activate the matcher or change historical scores before those steps and a separately approved integration plan.

## Regression verification

The full backend suite passed with `backend/.venv`:

```text
Ran 140 tests
OK
```

The run emitted an existing Starlette/httpx deprecation warning and a logged Supabase resume-download 404; neither failed a test. No production source, API, or scoring code was changed in this evaluation phase. Existing behavior and stored scores were therefore not modified; the regression suite, including API/scoring tests, passed.
