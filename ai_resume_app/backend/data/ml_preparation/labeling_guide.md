# Job–Employment Evidence Labeling Guide

**Status:** Instructions for future human annotation. No examples in this guide are labeled dataset records. The CSV templates are intentionally header-only.

## Annotation unit and independence

One row in `job_resume_role_annotations_template.csv` represents one reviewer’s judgment of one candidate employment role against one job. A resume with multiple supported roles can produce multiple review units for one job. Each reviewer must independently review the job and role evidence without seeing model output, automated rank, another reviewer’s label, or category metadata.

Use the pseudonymous job, candidate, resume, and role IDs from the controlled project registry. Do not enter names, emails, phone numbers, profile links, addresses, photos, or other direct identifiers.

## Relevance labels

- `directly_relevant`: Explicit responsibilities substantially support important duties of the target role. Related role-specific tools or skills corroborate the work. A matching title alone never qualifies.
- `partially_relevant_transferable`: Explicitly documented duties transfer to part of the target role, but evidence is not a direct match or leaves important duties unsupported. Explain the overlap and gap.
- `unrelated`: The resume documents a sufficiently clear, different type of work with no meaningful overlap with the target’s core responsibilities. Do not use this merely because a keyword is absent.
- `insufficient_evidence`: The available record does not support a reliable relevance decision, including missing duties, generic claims, mixed/ambiguous role boundaries, or conflicting evidence. This label means “cannot determine,” not “unqualified.”

Separately mark `evidence_status` as `sufficient`, `partial`, or `insufficient`. Record dates with `date_verification_status` (`verified`, `ambiguous`, `missing`, `needs_review`). Relevance and duration are different judgments: a directly relevant but undated role may still have `directly_relevant` with dates marked `missing`.

## Evidence rules

1. Compare actual candidate-role responsibilities with job responsibilities and explicit required skills.
2. Use title as context only. A title-only match is `insufficient_evidence` unless the role duties corroborate it.
3. Use a tool/skill only when the resume ties it to that employment record. Global Skills-section terms do not prove work experience.
4. Quote concise source snippets in `evidence_snippets` and explain the label in `evidence_rationale`. Do not copy entire resumes.
5. Do not invent responsibilities, tools, dates, employers, duration, seniority, or qualifications.
6. Missing or ambiguous dates never become verified duration. Do not infer months from year-only or total-career claims; preserve source evidence and request review.
7. Record internship status explicitly. Judge duty relevance using the same evidence standard; do not silently discount or equate internship duration.
8. For career changes, label only documented transferable duties. Do not infer future ability or convert transferable time to direct time.
9. For incomplete resumes, prefer `insufficient_evidence` over assuming either relevance or irrelevance.
10. Do not use protected traits, names, photos, demographic proxies, prestige assumptions, or unrelated personal details.

## Domain prompts

These are hypothetical prompts to guide consistent attention, not ground-truth examples:

- **Software/IT:** Look for software building, debugging, deployment, API, or maintenance duties. A programming language in global skills alone is insufficient.
- **Healthcare:** Look for explicit patient-care, clinical, nursing, or treatment duties. A hospital employer alone does not establish clinical role relevance.
- **Engineering:** Look for design, calculations, CAD, technical drawings, testing, or engineering specifications tied to the role.
- **Marketing:** Look for campaign, SEO, audience/content, channel, or campaign-performance duties rather than generic social-media mentions.
- **Accounting/Finance:** Look for bookkeeping, reconciliations, reporting, payables/receivables, close, or financial analysis.
- **Human Resources:** Look for recruiting, screening, onboarding, employee relations, workforce, or HR operations.
- **Sales:** Look for prospecting, lead generation, client acquisition, pipeline, negotiation, or closing. Customer service alone is not automatically sales.

For any domain, use job-specific duties and requirements; do not infer relevance from broad industry alone.

## Reviewer confidence and disagreement

Set `reviewer_confidence` to `high`, `medium`, or `low` based on evidence clarity, not the candidate’s apparent quality. Set `review_status` to `submitted` when the independent label and rationale are complete.

For two-reviewer labeling:

1. Preserve a separate row for each reviewer and keep original labels immutable.
2. Compare labels only after both reviewers submit.
3. If labels differ, set an appropriate `disagreement_code` (for example `direct_vs_transferable`, `unrelated_vs_insufficient`, `date_evidence`, or `role_boundary`).
4. An independent adjudicator records `adjudicated_label`, `adjudicator_id`, and `adjudication_rationale`; do not overwrite either reviewer’s answer.
5. Report raw disagreement and adjudication rates. Do not treat adjudicated labels as perfectly objective ground truth.

## Split metadata

Populate candidate/resume duplicate groups and near-duplicate job groups before assigning splits. All candidate versions and near-identical jobs must remain within their designated split. Keep synthetic tests out of real-data training, validation, and test sets. The held-out test job list must be sealed before model selection.

The `assigned_split` column is a data-management key, not a feature. Never supply reviewer IDs, split identifiers, adjudication fields, or source metadata to a model.

## Illustrative scenarios (not annotation records)

- A job title matches, but the listed duties are lead generation while the target role requires clinical care: do **not** label direct based on title.
- A general office role includes documented bookkeeping and reconciliations, while an accounting job requires those duties: consider partial or direct based on how much of the target’s core work is explicitly supported.
- A candidate lists CAD globally, but their employment record has no design duties: global CAD does not establish engineering experience; use insufficient evidence if the rest of the record is unclear.
- A role has relevant duties but no dates: preserve its relevance label and mark duration dates missing/review-needed; award no verified years.
