# Job-Specific Ranking Evaluation Preparation

## Purpose and current boundary

This folder prepares an offline human-label evaluation of the existing deterministic
resume ranking. It does not contain model outputs, scores, or recruiter relevance
judgments, and it does not change application behavior.

The live job record supplies `title`, `description`, `requiredSkills`,
`requiredExperience`, and `requiredEducation`. The backend accepts a missing
`requiredSkills` value via the legacy `requirements` field. The parser supplies
resume skills, experience, education, and project text. The scorer compares those
fields with a job and returns a normalized `finalScore` (0–100), plus component
scores. Its component maxima remain Skills 40, Experience 25, Education 20, and
Projects 15; unavailable components can be omitted from the normalization.
Recruiter candidate ordering groups by job, places scored applications first,
then sorts by descending resume score. Evaluation must use that existing output
and ordering without changing weights or ranking logic.

## What the available resume archive can and cannot provide

`archive (2).zip` contains 2,484 PDF resumes and a `Resume/Resume.csv` catalog
with `ID`, `Resume_str`, `Resume_html`, and `Category` (24 broad occupational
categories). It does not provide job descriptions, job requirements, job IDs,
or recruiter relevance judgments. A category is only a source-dataset label; it
must never be treated as a job-specific relevance label.

`candidates.csv` is a deterministic pilot inventory of 30 actual archive resume
references: the five lowest numeric resume IDs in each of ACCOUNTANT, ENGINEERING,
HEALTHCARE, HR, INFORMATION-TECHNOLOGY, and SALES. Candidate aliases C001–C030
are stable within this prepared sample. The CSV stores archive member paths and
does not copy or expose resume text. Resolve each member from the existing ZIP.

No actual job requirements were found in the offline source files. Therefore
`jobs_template.csv` and `relevance_labels_template.csv` intentionally contain
headers and a blank row only. Fill them only from authentic, permissioned job
records and independent recruiter judgments. Do not invent job descriptions,
IDs, labels, or rationales.

## Labeling rubric and procedure

Label each job–resume pair independently, using the job text and resume evidence:

| Label | Meaning |
|---:|---|
| 0 | Not relevant: the resume provides no meaningful evidence for the job's core requirements. |
| 1 | Partially relevant: some requirements are supported, but important requirements are missing, unclear, or weakly evidenced. |
| 2 | Highly relevant: strong, direct evidence supports the job's core requirements, with no major essential gap. |

Use the rationale field to cite concise, observable evidence and gaps; do not
restate the automated score. Do not infer skills, qualifications, or experience
from a resume category. Hide the system score/rank from labelers. Have two
reviewers label independently where practical; discuss disagreements and record
the agreed final label and rationale in the template. Preserve original labels
separately if adjudication is performed.

For a small pilot, obtain three real job descriptions and have one reviewer label
all 30 candidates for each job (90 job–resume judgments). If possible, have a
second reviewer independently label at least 20% of pairs and adjudicate
disagreements. This is a feasibility pilot, not enough to claim broad
generalization; add jobs and candidates if the relevance mix is too sparse.

## Evaluation protocol

1. Freeze the three authentic job records before scoring; retain their source and
   exact text/requirements in `jobs_template.csv`. Use the same `requiredSkills`,
   `requiredExperience`, and `requiredEducation` inputs as the live scorer.
2. Resolve and parse each listed PDF locally. Run the existing parser and scorer
   without edits, once per distinct resume and job. Keep the resulting
   `finalScore`, `scoringStatus`, and component availability in a separate
   evaluation-results file; do not put automated values in the human-label
   template.
3. Rank scored candidates within each job using the existing recruiter ordering
   and score; report scoring coverage separately. Capture the exact rendered
   order for equal scores. The current comparator has no explicit tie-breaker,
   so do not claim a new deterministic production tie rule. If equal-score
   ordering changes between runs, report the tied group and perform a tie-order
   sensitivity analysis rather than selecting a favorable ordering.
4. Compute per-job NDCG@5 using gains `2^label - 1`, then report the mean across
   jobs. Report Precision@5 with `label >= 1` as the primary “at least partially
   relevant” threshold, and also show strict Precision@5 with `label == 2` so
   the high-relevance interpretation is visible. Use 5 as the Precision@5
   denominator (an unfilled rank counts as not relevant), and normalize NDCG
   against the ideal ordering of available scored candidates up to five. Report
   the number of scored candidates per job.
5. Optionally report MAP per job using binary relevance `label >= 1`, and the
   mean AP across jobs. Report per-job results as well as the macro-average;
   three jobs provide limited precision and should not be overinterpreted.
6. Do not select weights, thresholds, or tie rules using the same labels used
   for the final metric. If tuning is later attempted, use job-grouped
   development data and a separate held-out set of whole jobs.

NDCG@5 measures ordering quality with graded labels; Precision@5 measures how
many top-five results meet the predeclared relevance threshold; MAP summarizes
the positions of relevant candidates across the full ranked list. These metrics
evaluate job-specific relevance, unlike the Phase 2 historical shortlist
classification metrics.

## Duplicate and split leakage controls

- Check byte-identical PDFs using SHA-256 and text-identical resumes using a
  normalized extracted-text hash. Manually review likely near duplicates;
  document the matching rule and canonical resume group.
- Treat multiple versions of one candidate as one resume group. Assign each
  canonical resume/candidate group wholly to one partition.
- Keep every pair for a `job_id` in one partition. For any future model or
  tuning exercise, split by whole jobs, not random job–resume rows.
- If a resume/candidate appears in multiple jobs, do not allow it to bridge
  training and test partitions. Group connected job/resume components together
  or remove cross-partition duplicates before evaluation.
- The deterministic scorer itself has no fitted training split; these controls
  apply when judging generalization or tuning against relevance labels.

## Files

- `candidates.csv`: reproducible archive member references for 30 real resumes.
- `jobs_template.csv`: blank schema for authentic job records.
- `relevance_labels_template.csv`: blank pairwise human-label schema. Required
  fields are `job_id`, `candidate_id`, `resume_id`, `relevance_label`, and
  `rationale`.
