# Dataset Provenance, Consent, and Privacy Checklist

**Use before any resume/job record is added to a human-label or model dataset.** This is a checklist, not legal advice. Store completed approvals in the project’s restricted governance location; do not put sensitive evidence in public reports.

## Source and permission

- [ ] Record dataset/job source, collection date, owner, license/terms, and permitted purpose.
- [ ] Confirm the project may retain, annotate, transform, and use the resume and job description for the stated research/training purpose.
- [ ] Confirm whether explicit candidate consent, institutional review, or additional approval is required; obtain it before processing.
- [ ] Confirm terms permit local parsing and any proposed model training/evaluation; do not assume public accessibility grants reuse rights.
- [ ] Record applicable retention and deletion requirements and a responsible data steward.
- [ ] For recruiter-provided jobs, confirm permission to retain job text and requirements for annotation and reporting.

## Data minimization and de-identification

- [ ] Assign stable pseudonymous `job_id`, `candidate_id`, `resume_id`, and role IDs.
- [ ] Keep any re-identification/linkage key separate, encrypted, and access-restricted.
- [ ] Remove names, emails, phones, profile URLs, exact addresses, photos, and unrelated personal details before annotation.
- [ ] Do not add protected characteristics or sensitive personal data to features or labels.
- [ ] Minimize evidence quotes to short, necessary, non-identifying excerpts; never include full resume text in templates or reports.
- [ ] Review job text for recruiter/company confidential information; redact or restrict it as required.

## Security and operations

- [ ] Restrict data access to authorized project reviewers; use approved encrypted storage and transfer.
- [ ] Document who can access raw files, redacted annotation data, and the linkage key.
- [ ] Set a retention period and process for secure deletion of raw files, exports, backups, and temporary files.
- [ ] Do not upload candidate data to external tools or services without explicit authorization and an approved privacy review.
- [ ] Keep provenance/source metadata in restricted records; use only anonymized IDs in experiment outputs.

## Label integrity and fairness

- [ ] Confirm labels are independent human judgments under the documented rubric, not generated from resume categories, keyword overlap, or model predictions.
- [ ] Keep synthetic cases clearly marked and separate from real training/evaluation data.
- [ ] Ensure reviewers cannot see automated scores/ranks while labeling.
- [ ] Preserve independent reviewer labels and adjudication history.
- [ ] Check for class/domain representation and likely systematic missing evidence before making performance claims.
- [ ] Review potential proxy bias (for example names, institution prestige, geography, employer brand, career gaps) and exclude unjustified features.
- [ ] Provide `insufficient_evidence` and a human-review path; never equate missing resume detail with lack of qualification.

## Release gate

Do not add a record to the training dataset until required permission, provenance, minimization, access, and retention checks are complete. If a check fails or is unknown, mark the record `permission_status=not_cleared` and exclude it from annotation, training, and evaluation pending review.
