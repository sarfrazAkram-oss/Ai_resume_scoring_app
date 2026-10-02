# ML Screening Experiment

This is a leakage-controlled binary classification experiment, not the production Resume Ranking Engine.

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

`skills_match_score` was excluded because it is a precomputed match-like feature and can circularly encode the shortlist decision. No other direct outcome/match field was used.

## 7. Excluded Features

- `skills_match_score`: leakage-risk precomputed matching feature.
- `shortlisted`: target, never a feature.
- No other source fields were available.

## 8. Features Used

`years_experience`, `education_level`, `project_count`, `resume_length`, `github_activity`

## 9. Data Cleaning

Numeric columns were coercively parsed with invalid values becoming missing; numeric missing values use training-set medians. `education_level` is one-hot encoded with a training-fitted most-frequent imputer. The target accepts only Yes/No; duplicate rows were checked and no exact duplicates were found.

## 10. Train/Test Split

Stratified 80/20 split: train=24000, test=6000. Preprocessing is inside each sklearn Pipeline and is fitted only on training data.

## 11. Class Distribution

Yes=20966 (69.887%), No=9034 (30.113%). Accuracy is therefore not sufficient by itself; precision, recall, F1, ROC-AUC, and the confusion matrix are reported.

## 12. Logistic Regression Results

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

## 13. Random Forest Results

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

## 17. Model Comparison

The metrics above compare two interpretable baselines on the same held-out stratified test set. No model selection was promoted to production.

## 18. Limitations

The dataset contains engineered candidate-side features rather than resume/job pairs. It does not test recruiter-created requirements, text extraction, domain relevance, project evidence, or the production /100 score. The shortlist label may reflect an unknown historical process.

## 19. Relationship to the Existing /100 Resume Ranking Engine

The deterministic engine and its 40/25/20/15 weights were not modified. This experiment is isolated and does not write scores, shortlist candidates, call Flutter, or connect to Firestore/Supabase.

## 20. Final Conclusion

This experiment measures how two simple classifiers model the supplied historical screening labels without the explicitly precomputed match feature. It does not prove accuracy for recruiter-job matching and must not replace the deterministic production score.
