# ML Training Data Preparation and Model Selection Plan

**Project:** AI Resume Ranking System  
**Phase:** 7B — preparation and planning only  
**Status:** No new labels collected; no model trained or deployed in this phase.

## Executive recommendation

The primary supervised ML task should be **employment-role-to-job evidence relevance classification**. Given a recruiter job and one candidate employment record, predict one of:

- `directly_relevant`
- `partially_relevant_transferable`
- `unrelated`
- `insufficient_evidence`

This is a narrower and more defensible FYP task than predicting a complete candidate ranking. It builds on the Phase 6 matcher’s explainable unit of analysis, makes responsibility evidence central, and permits uncertainty to remain visible. It does not claim that a classifier alone improves ranking.

The best first learned baseline, after collecting independent human labels, is **word/character TF-IDF features with regularized Logistic Regression**, compared against the unchanged deterministic matcher. A Linear SVM is a useful second sparse-text baseline. Do not select or report either model as useful for live ranking until it is evaluated on held-out jobs and candidates.

**Phase 7C is not ready to train a job-relevance model:** there are no independently labeled job–resume-role pairs, no verified job/resume pairings, and no known permissioned, representative annotation set. Begin with a human-label feasibility pilot and provenance checks.

## 1. Dataset inventory and suitability

| Dataset | Contents and fields | Resume text | Job description / requirements | Human job–resume relevance labels | Appropriate use |
|---|---|---:|---:|---:|---|
| `backend/data/raw/archive (1).zip` → `ai_resume_screening.csv` | 30,000 rows; `years_experience`, `skills_match_score`, `education_level`, `project_count`, `resume_length`, `github_activity`, `shortlisted` | No | No | No. `shortlisted` is a historical binary outcome, not a relevance label for a specified job. | The existing offline shortlist classification experiment only. Not a job-relevance model dataset. |
| `backend/data/raw/archive (2).zip` → `Resume/Resume.csv` and PDF members | 2,484 catalog rows; `ID`, `Resume_str`, `Resume_html`, `Category`; 2,484 PDFs in 24 broad categories | Yes | No | No. Categories must not be used as relevance judgments. | Parser/section coverage and resume-text feature testing, subject to provenance and permission review. |
| `backend/data/raw/archive (3).zip` → `01_people.csv` | 54,933 rows; `person_id`, `name`, `email`, `phone`, `linkedin` | No | No | No | Identity table only; contains personal data and is not needed in a relevance training corpus. Do not copy contact fields into annotation files. |
| `archive (3).zip` → `02_abilities.csv` | 1,219,473 rows; `person_id`, `ability` | No | No | No | Dataset-derived vocabulary construction; no job matching label. |
| `archive (3).zip` → `03_education.csv` | 75,999 rows; `person_id`, `institution`, `program`, `start_date`, `location` | No | No | No | Education vocabulary construction and schema exploration; no job matching label. |
| `archive (3).zip` → `04_experience.csv` | 265,404 rows; `person_id`, `title`, `firm`, `start_date`, `end_date`, `location` | No | No | No | Experience-title vocabulary construction. Titles/dates without job-specific duties and labels do not train a relevance model. |
| `archive (3).zip` → `05_person_skills.csv` | 2,483,376 rows; `person_id`, `skill` | No | No | No | Dataset-derived vocabulary construction; no job matching label. |
| `archive (3).zip` → `06_skills.csv` | 226,760 rows; `skill` | No | No | No | Dataset-derived skill vocabulary construction; no job matching label. |
| `backend/data/raw/archive.zip` → `resume_screening_automation.csv` and standalone `backend/data/raw/resume_screening_automation.csv` | 100 rows each; `resume_text`, `job_title`, `suitability_score`; the standalone CSV duplicates the ZIP member | Yes, short text | A title only; no requirements or description | No verified human job–resume label provenance. A suitability score is not assumed to be a human judgment. | Not suitable for supervised job relevance or ranking unless provenance and label semantics are independently established. |
| `backend/data/processed/skills_vocabulary.json` | Up to 5,000 terms, sourced from relational ability/skill tables | No | No | No | Runtime lexical vocabulary; not a trained model. |
| `backend/data/processed/education_vocabulary.json` | Up to 5,000 education-program terms from `03_education.csv` | No | No | No | Runtime lexical vocabulary; not a trained model. |
| `backend/data/processed/experience_vocabulary.json` | Up to 5,000 experience-title terms from `04_experience.csv` | No | No | No | Runtime lexical vocabulary; not a trained model. |
| `backend/data/ranking_eval/candidates.csv` | 30 references to resumes sampled from six archive categories | Resolved from archive | No | No | Sampling inventory only. Candidate/category is not a relevance label. |
| `backend/data/ranking_eval/jobs_template.csv` and `relevance_labels_template.csv` | Header-only schemas with no job records or labels | No data | No data | No | Preparation templates only. |
| `backend/data/job_relevance_eval_cases.json` | 20 explicitly synthetic matcher cases | Synthetic examples only | Synthetic examples only | Provisional engineering expectations, not human labels | Matcher engineering checks only; exclude from real-world training and evaluation metrics. |

Dataset inventory facts are also documented in `backend/data/DATASET_ANALYSIS.md`. Existing evaluation reports distinguish parser coverage from accuracy. None of the available data provides authentic, independently judged job–employment evidence pairs.

### Suitability summary

- **Supervised job–resume relevance:** Not currently supported by the available labels.
- **Parser evaluation:** The 2,484-resume archive supports text/section coverage checks, not parser accuracy absent annotated section boundaries.
- **Vocabulary construction:** The relational skill, ability, program, and title tables support lexicon construction; these are not relevance labels or learned parameters.
- **Offline classification only:** The 30,000-row `shortlisted` data supports its historical binary outcome experiment, with documented label-provenance limits.
- **Potential future reuse:** The resume text archive could supply candidates only after permission/provenance checks and pairing with real job records plus independent labels. Resume categories cannot substitute for those labels.

## 2. Prediction target and task selection

### Chosen primary task

Predict the relevance of **one employment record to one recruiter job**, not the candidate's overall employability. Input fields should include:

- Job title, description/responsibilities, and explicit required skills.
- Candidate employment title, responsibilities, and technologies/tools explicitly tied to that employment record.
- Employment extraction confidence and date-evidence status as separate review metadata.

Do not use global resume skills as proof that a skill was used in a particular job. The first relevance model should not infer verified experience duration from textual classification; date parsing and verified duration remain separate rule-based evidence. Do not pass names, contact details, protected attributes, or unrelated demographic proxies to the model.

Output one of the four relevance labels, plus model version and uncertainty/review status. Probabilities from Logistic Regression are not automatically calibrated confidence; calibration and abstention thresholds require separate validation data.

### Alternative tasks considered

| Option | Assessment |
|---|---|
| A. Overall job–resume relevance classification | Closest to recruiter ranking, but requires a clear candidate-level aggregation policy and authentic job/resume judgments. It combines work history, skills, education, and projects and is a wider first task. |
| **B. Role-specific experience relevance classification** | **Recommended.** Bounded to job/employment evidence, explainable against duties, aligned with the inactive matcher, and can keep uncertain or undated records distinct. It still needs human labels. |
| C. Semantic similarity of requirements and evidence | A similarity score is not itself a relevance label or ranking judgment. Similar wording can be misleading; it needs a calibrated, human-validated decision rule and evidence checks. Consider only as a later feature or baseline. |

This subtask should initially be an **advisory evidence signal**, not a new input to the existing experience points. Preserve Skills/Experience/Education/Projects weights at 40/25/20/15. Do not combine prediction labels into a score without a separately approved scoring policy and held-out ranking evaluation.

## 3. Human annotation plan

Use the blank templates in `backend/data/ml_preparation/`. A **review unit** is one job × one candidate employment record × one reviewer. If a resume has multiple roles, annotate each supported role independently; do not make a single candidate label from a global skill list.

### Labels and criteria

| Label | Annotator rule |
|---|---|
| `directly_relevant` | The role has explicit duties substantially supporting important responsibilities of the target job. Corroborating role-specific tools/skills strengthen the label. A title match alone is insufficient. |
| `partially_relevant_transferable` | The record documents duties that plausibly transfer to some target responsibilities, but does not support a direct role match or leaves important duties unsupported. State the actual overlap; do not award an arbitrary percentage of experience. |
| `unrelated` | The record contains enough clear role-specific evidence to establish a different kind of work and no meaningful target-duty overlap. Lack of a keyword, title, or detail is not evidence of unrelatedness. |
| `insufficient_evidence` | The available resume evidence cannot determine relevance, for example because responsibilities are missing, role boundaries are ambiguous, or evidence is too generic. This is a review/abstention label—not proof of no qualification and not a negative label. |

Record evidence sufficiency and duration verification separately from relevance. A relevant role with missing dates may be `directly_relevant` while its duration is `needs_review`; never infer dates or combine an undated duration claim with verified dated employment.

### Domain guidance and illustrative evidence

These are annotation examples only, not dataset rows, resume facts, or labels:

- **Software/IT:** Explicit software development, debugging, deployment, or API work is stronger than “worked in technology.” A listed programming language only in a global Skills section is not employment evidence.
- **Healthcare:** Patient-care or clinical duties support a nursing role; generic employment at a hospital does not establish nursing duties.
- **Engineering:** Design calculations, engineering drawings, CAD work, or prototype testing can support engineering. A generic “engineer” title without duties is insufficient.
- **Marketing:** Campaign planning, SEO, audience/content work, or measured campaign performance can support marketing. General social-media usage alone does not establish campaign responsibility.
- **Accounting/Finance:** Reconciliation, bookkeeping, financial reporting, accounts payable/receivable, or close processes are relevant duties. Generic office work is not enough.
- **HR:** Recruitment, screening, onboarding, employee relations, or HR operations are relevant duties. A “people person” claim is not evidence of HR work.
- **Sales:** Prospecting, lead generation, client acquisition, sales pipeline ownership, or closing evidence supports sales. Generic customer service does not automatically establish selling.

### Special cases

- **Titles:** Use as one signal only; require responsibilities for a direct label. Same-title/different-duty cases need careful review.
- **Skills:** Do not use global skills as proof of role-specific skill use. Record tools only if tied to the employment evidence.
- **Internships:** Annotate duties by the same relevance criteria; record internship status separately. Do not silently discount or equate duration; the future scoring policy must decide how internship time counts.
- **Career changes:** Use documented transferable duties, not assumptions about potential. Partial transfer is not direct experience.
- **Incomplete resumes:** Prefer `insufficient_evidence` when work details are absent or unclear. Do not infer the missing information.
- **Dates:** Preserve source date evidence and separately label `verified`, `ambiguous`, `missing`, or `needs_review`. Never guess year/month or turn total career claims into a role interval.
- **Disagreements:** Two reviewers label independently without seeing system predictions or each other's labels. Preserve both original labels and rationales. A separate adjudicator resolves disagreements and records the adjudicated label, adjudicator, and reason; never overwrite the originals.

Reviewer instructions and an adjudication log convention are in `backend/data/ml_preparation/labeling_guide.md`.

## 4. Template schema and provenance

- `jobs_template.csv`: one anonymized job per row, with title, domain, description/responsibilities, explicit skills/experience/education requirements, job grouping, source type/reference/date, and permission status.
- `job_resume_role_annotations_template.csv`: one job × candidate role × reviewer judgment per row. Includes anonymized IDs/group keys, role evidence, date status, source type, label, evidence rationale, reviewer confidence/status, and fields for disagreement/adjudication. It contains headers only; no fake labels or candidate text.
- `labeling_guide.md`: rubric, domain examples, reviewer workflow, and split safeguards.
- `provenance_consent_checklist.md`: permission, licensing, anonymization, security, retention, and audit checklist.

Templates must contain only the minimum redacted job/resume evidence needed for annotation. Do not put contact details, names, addresses, demographic attributes, or raw resume files in the training spreadsheet. Store source documents separately in access-controlled storage; use stable pseudonymous IDs and a restricted linkage key outside the modeling dataset.

## 5. Splits and leakage controls

1. Establish canonical candidate and resume duplicate groups using a privacy-safe process. Keep all versions/near-duplicates of a candidate in one partition.
2. Group identical or near-duplicate job descriptions/requirements into one job group. All variants stay in the same partition.
3. Keep test jobs unseen during model development. Hold out complete job groups, not random role/job rows.
4. Also keep candidate groups disjoint across train/validation/test. If a candidate appears across jobs, either assign the entire candidate group to one partition and remove cross-partition pairs, or use a blocked split that enforces both candidate and job grouping. Document dropped rows and class coverage; do not relax these controls merely to increase the test set.
5. Keep the final test partition sealed until feature/model choices and thresholds are fixed. Use training jobs for fitting, validation jobs for model selection/calibration, and test jobs for one final estimate.
6. Synthetic Phase 6C cases stay in engineering tests; never mix them into these splits or report them as independent real-world test examples.

With too few jobs for stable held-out metrics, report feasibility and uncertainty rather than precise accuracy. A grouped cross-validation over jobs can supplement the pilot, but is not a substitute for a later untouched test set of genuinely unseen jobs.

## 6. CPU-friendly baseline comparison

| Baseline | Data required | CPU / inference | Explainability and strengths | Risks |
|---|---|---|---|---|
| **TF-IDF + Logistic Regression** | Human-labeled role/job pairs; four classes represented across multiple jobs. | Low CPU and memory for sparse text; fast inference. | Inspectable token/phrase weights; `predict_proba` output can support review only after calibration. | Keyword overlap and vocabulary bias; probabilities are not calibrated by default; may miss paraphrases. |
| TF-IDF + Linear SVM | Same labeled pairs and split controls. | Low CPU/memory; fast sparse inference. | Strong linear text baseline; inspectable feature weights/margins. | Raw margins are not calibrated probabilities; needs a separate calibration set for confidence. |
| Existing deterministic relevance matcher | No training labels; curated rules and vocabulary. | Very low CPU; deterministic. | Explicit matched phrases/snippets and clear rules. | Brittle phrases, incomplete domain vocabulary, parser/role-boundary errors; Phase 6C found a synthetic paraphrase miss but no real accuracy estimate. |
| Pretrained sentence embeddings (later only) | Permissioned job-role text plus human labels for validation; model/version documentation. | Model-dependent CPU and memory; heavier than sparse linear inference. | May capture some paraphrases better than exact-term rules. | Can encode bias, hide rationale, require model distribution/dependency and may still mismatch domain-specific work. No model or dependency should be downloaded in this preparation phase. |

**Recommendation:** begin with the unchanged deterministic matcher as the transparent reference and TF-IDF + regularized Logistic Regression as the learned baseline. If resource/time permits, compare Linear SVM. Use separate field markers or feature blocks for job duties, job skills, role title, role duties, and in-role tools; test whether the model is merely learning title/keyword shortcuts. Sentence embeddings are a later, optional experiment, not the starting point.

## 7. Evaluation plan

### Classification

On independent labels and held-out job groups, report:

- Four-class confusion matrix and per-class precision, recall, and F1.
- Macro F1 as the primary class-balanced metric; include class support.
- Insufficient-evidence prediction rate, reviewer/manual-review rate, and coverage after abstention.
- Agreement between independent reviewers (and adjudication rate) to contextualize label noise.
- Calibration/uncertainty measures only if probabilities are calibrated on validation jobs and evaluated on unseen test jobs.

Do not use ordinary accuracy alone. Report rule-based and ML results on the same held-out pairs, and report both paired case results and aggregate metrics. An ML model should not be accepted solely because it exceeds a metric on training/validation data.

### Ranking

Classification labels do not automatically prove ranking quality. For candidate-ranking evaluation, obtain independently reviewed candidate-level relevance grades or a blinded HR ranking for each authentic job. Freeze any mapping from role-level labels to candidate-level grades before testing; define how `insufficient_evidence`, multiple roles, and internships affect that mapping. Then report per-job NDCG@K and Precision@K (and optionally MAP), macro-averaged across jobs. Do not treat pairwise comparisons or category labels as graded relevance without a rubric and reviewer judgment.

## 8. Minimum viable data-collection pilot

1. **Permission/provenance first.** Confirm the candidate resumes and authentic job descriptions can be used for this FYP. Existing archive references alone do not establish permission.
2. Run an annotation-feasibility pilot with approximately **10 authentic jobs × 30 varied candidate resumes = 300 job/resume pairs** (and role-level evidence units where applicable). Include relevant, partially relevant, unrelated, and insufficient-evidence examples; do not sample only obvious matches.
3. Have two reviewers independently annotate at least 20–25% of pairs, including each domain and difficult cases; adjudicate every disagreement. If feasible, double-label all pairs for the first pilot.
4. Use this pilot to refine instructions, assess reviewer agreement, and estimate annotation effort. **Do not claim robust model performance from 300 pairs or 10 jobs.**
5. For a first exploratory grouped model comparison, target at least **20–30 distinct, non-duplicate jobs** and several hundred to 1,000+ pairs, while prioritizing label quality and adequate support for every class over raw row count. Hold out whole jobs. Increase the dataset if test jobs/classes are too sparse for meaningful per-class reporting.

These are planning targets, not statistical guarantees. Required sample size depends on job diversity, class balance, reviewer consistency, and observed uncertainty.

## 9. Privacy, consent, and bias

- Confirm source license, consent/permission, purpose limitation, and retention before using any candidate record; public availability is not blanket permission.
- Remove direct identifiers and minimize quasi-identifiers. Do not train on names, email, phone, LinkedIn, photos, exact address, or protected attributes.
- Avoid proxies such as institution prestige, graduation year, geography, unexplained gaps, or employer brand unless job-related necessity and fairness impact are explicitly reviewed.
- Preserve uncertainty: missing detail is not evidence of no experience. Provide an abstain/manual-review route.
- Review outcomes by domain and relevant demographic groups only where lawful, consented, and safely governed; do not put sensitive demographic data into the model feature set.
- Restrict dataset and linkage-key access, encrypt storage, document retention/deletion, and never publish raw resume text or employer/candidate identities in reports.
- Obtain appropriate academic/ethics approval and reviewer confidentiality commitments before annotation.

## 10. Future implementation plan

1. Complete consent/provenance review and human-label pilot; freeze rubric and resolve label disagreements.
2. Validate employment-role extraction independently, particularly title/duty/date association; retain raw source only in protected storage.
3. Build a deterministic, versioned feature-extraction/evaluation pipeline and split by candidate and job groups.
4. Compare the rule matcher, Logistic Regression, and optionally Linear SVM on identical grouped folds; keep the held-out job test sealed.
5. Evaluate class errors, confidence calibration/abstention, subgroup/domain behavior, and ranking metrics from independent HR judgments.
6. If and only if ML complements the rules, introduce it in FastAPI as a versioned **shadow/advisory** output first. Keep current 40/25/20/15 score, Firestore score fields, recruiter ordering, and legacy jobs unchanged.
7. Log model version, inputs/policy snapshot identifiers, output, uncertainty, and errors without writing over historical scores. Make human review available; never automatically reject a candidate from an unvalidated prediction.
8. A future scoring change requires explicit approval, job/scorer versioning, migration/rollback and complete-rescoring strategy, regression coverage, and a separate ranking evaluation.

Likely future touchpoints (not changed in Phase 7B):

- New data collection/evaluation code and manifests under `backend/data/ml_preparation/` and `backend/scripts/`.
- A new isolated model training/inference service under `backend/app/services/` (do not overload the inactive heuristic or call it from live scoring before approval).
- `backend/app/main.py` only if a reviewed shadow/inference interface is approved.
- `backend/app/services/final_scorer.py` only if a later, separately approved scoring policy uses model output.
- Tests under `backend/tests/` for deterministic preprocessing, group splitting, model artifact/version loading, uncertainty, failure behavior, and unchanged legacy scoring.
- Flutter should not need changes for an initial backend-only shadow evaluation. Any recruiter-facing explanation or review UI would require its own approved design and tests.

## 11. Phase 7C readiness criteria

**Current state: NOT READY.** Missing prerequisites:

- Permissioned, provenance-documented resume/job data and authentic job requirements.
- Independent human role/job relevance labels and evidence rationales.
- Enough distinct jobs and candidates for job- and candidate-grouped train/validation/test partitions.
- Label coverage for all four classes and a documented adjudication/quality process.
- Independently validated role-level responsibilities/date extraction.
- An agreed candidate-ranking aggregation policy for multiple roles, internships, and insufficient evidence.

Proceed to Phase 7C training only after these are addressed; an exploratory fit may then be conducted strictly offline. A move toward deployment additionally requires a sealed held-out job evaluation showing meaningful, stable complementarity to the rule baseline, calibrated uncertainty or a conservative abstention method, privacy/fairness review, and explicit approval for shadow integration. Existing shortlist accuracy does not satisfy these criteria.
