# ML Screening Experiment

This is an offline historical-label classification experiment, not the production Resume Ranking Engine.

## 1. Experiment Objective

Compare Logistic Regression and Random Forest for the supplied screening target `shortlisted` using defensible candidate-side features only.

## 2. Dataset Used

- Archive: `archive (1).zip`
- CSV member: `ai_resume_screening.csv`
- Rows used: 30000
- Random seed: 42

## 3. Why This Dataset Was Chosen

It is the only supplied dataset with a binary shortlist-like target and 30,000 structured records. The report inspection confirmed that the other datasets lack matching job/resume outcomes or are duplicated/suited for vocabulary/parser work.

## 4. Why This Is Not the Production Ranking Model

The dataset has no raw resume text, recruiter job requirements, or resume/job pairs. It cannot validate the application’s recruiter-specific Skills/Experience/Education/Projects score.

## 5. Target Variable

`shortlisted`: Yes=20966, No=9034; positive rate=69.887%.

## 6. Leakage Analysis

`skills_match_score` was excluded because it is a precomputed match-like feature and can circularly encode the shortlist decision. No other direct outcome/match field was used. The dataset does not document label-generation provenance, so indirect or proxy leakage cannot be ruled out.

## 7. Excluded Features

- `skills_match_score`: leakage-risk precomputed matching feature.
- `shortlisted`: target, never a feature.
- No other source fields were available.

## 8. Features Used

`years_experience`, `education_level`, `project_count`, `resume_length`, `github_activity`

### Dataset distributions and live-parser compatibility

| Feature | Dataset distribution | Live resume feature compatibility |
|---|---|---|
| `years_experience` | numeric-like; missing=0; min=0; median=7; max=15 | Approximate only: live experience entries can yield candidateYears, but the dataset's source calculation and units are undocumented. |
| `education_level` | Bachelors: 13461; High School: 2991; Masters: 10524; PhD: 3024 | Partial only: live education parsing provides degree/level; dataset categories and qualification-selection rules are not equivalent by definition. |
| `project_count` | numeric-like; missing=0; min=0; median=10; max=25 | Partial only: live projects can be counted, but project extraction is incomplete and the dataset's counting definition is undocumented. |
| `resume_length` | numeric-like; missing=0; min=150; median=574; max=900 | Incompatible until defined: live text length can be measured, but the dataset unit and preprocessing definition are undocumented. |
| `github_activity` | numeric-like; missing=0; min=0; median=321; max=842 | Unavailable: live resume parsing does not extract a defined GitHub activity metric; do not infer activity from a URL or mention. |

These are feature-schema comparisons, not proof that the live parser produces equivalent values. `skills_match_score` is excluded as leakage risk; the target is never a feature.

## 9. Data Cleaning

Numeric columns were coercively parsed with invalid values becoming missing; numeric missing values use training-set medians. `education_level` is one-hot encoded with a training-fitted most-frequent imputer. The target accepts only Yes/No. Source rows=30000; rows with valid labels=30000; invalid-label rows excluded=0; exact duplicate rows=0.

## 10. Train/Test Split

Stratified 80/20 split: train=24000, test=6000. Preprocessing is inside each sklearn Pipeline and is fitted only on training data.

## 11. Class Distribution

Yes=20966 (69.887%), No=9034 (30.113%). Accuracy is therefore not sufficient by itself; precision, recall, F1, ROC-AUC, and the confusion matrix are reported.

## 12. Majority-Class Baseline

Predicts the training majority class (`Yes`) for every test row. Accuracy=0.6988, Precision=0.6988, Recall=1.0, F1=0.8227.

Confusion matrix `[[TN, FP], [FN, TP]]`: `[[0, 1807], [0, 4193]]`

## 13. Logistic Regression Results

Accuracy=0.8935, Precision=0.9185, Recall=0.9301, F1=0.9243, ROC-AUC=0.9564

Confusion matrix `[[TN, FP], [FN, TP]]`: `[[1461, 346], [293, 3900]]`

Top associated transformed features (not causal effects):

- `numeric__years_experience`: 2.515965
- `categorical__education_level_PhD`: 1.948343
- `numeric__project_count`: 1.360241
- `categorical__education_level_Masters`: 1.063795
- `categorical__education_level_High School`: -0.985604
- `numeric__github_activity`: 0.28575
- `categorical__education_level_Bachelors`: 0.092863
- `numeric__resume_length`: 0.022295

## 14. Random Forest Results

Accuracy=0.8822, Precision=0.9092, Recall=0.9237, F1=0.9164, ROC-AUC=0.9494

Confusion matrix `[[TN, FP], [FN, TP]]`: `[[1420, 387], [320, 3873]]`

Top associated transformed features (not causal effects):

- `numeric__years_experience`: 0.286908
- `numeric__github_activity`: 0.277152
- `numeric__resume_length`: 0.213775
- `numeric__project_count`: 0.187204
- `categorical__education_level_High School`: 0.009773
- `categorical__education_level_PhD`: 0.009446
- `categorical__education_level_Masters`: 0.007954
- `categorical__education_level_Bachelors`: 0.007788

## 15. Model Comparison

The classifiers and majority baseline use the same held-out stratified test set. Model comparison is limited to this historical classification task; no model is promoted to production.

## 16. Limitations

The dataset contains engineered candidate-side features rather than resume/job pairs. Feature source definitions and units are undocumented. GitHub activity is not extracted by the live parser; resume length units and project-count semantics cannot be confirmed. It does not test recruiter-created requirements, text extraction, domain relevance, project evidence, or the production /100 score. The shortlist label may reflect an unknown historical process.

## 17. Relationship to the Existing /100 Resume Ranking Engine

The deterministic engine and its 40/25/20/15 weights were not modified. This experiment is isolated and does not write scores, shortlist candidates, call Flutter, or connect to Firestore/Supabase.

## 18. Ranking labels needed

To evaluate job-specific ranking, collect recruiter-judged relevance for each job–resume pair (for example, graded relevance levels with a documented rubric), including multiple candidates per job. Keep jobs/candidates separated between training and test. Then report NDCG@K and Precision@K (and optionally Recall@K/MAP) against those held-out judgments.

## 19. Readiness

Not ready for live integration: the current features cannot all be reliably reproduced from live resumes and the historical `shortlisted` label is not job-specific relevance. The experiment measures historical shortlisting classification only, not CV-ranking quality.
