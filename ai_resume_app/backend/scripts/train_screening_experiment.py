"""Offline binary screening experiment; not production ranking."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_PATH = ROOT / "data" / "ML_EXPERIMENT.md"
SEED = 42
TARGET = "shortlisted"
LEAKAGE_RISK_FIELDS = {"skills_match_score"}
EXPECTED_FEATURES = {
    "years_experience",
    "education_level",
    "project_count",
    "resume_length",
    "github_activity",
}
FEATURE_COMPATIBILITY = {
    "years_experience": (
        "Approximate only: live experience entries can yield candidateYears, but "
        "the dataset's source calculation and units are undocumented."
    ),
    "education_level": (
        "Partial only: live education parsing provides degree/level; dataset "
        "categories and qualification-selection rules are not equivalent by definition."
    ),
    "project_count": (
        "Partial only: live projects can be counted, but project extraction is "
        "incomplete and the dataset's counting definition is undocumented."
    ),
    "resume_length": (
        "Incompatible until defined: live text length can be measured, but the "
        "dataset unit and preprocessing definition are undocumented."
    ),
    "github_activity": (
        "Unavailable: live resume parsing does not extract a defined GitHub "
        "activity metric; do not infer activity from a URL or mention."
    ),
}


def _find_dataset() -> tuple[Path, str]:
    for path in sorted(RAW_DIR.glob("*.zip")):
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if Path(member).name == "ai_resume_screening.csv":
                    return path, member
    raise FileNotFoundError("Could not locate ai_resume_screening.csv in backend/data/raw/")


def _load_data() -> tuple[pd.DataFrame, Path, str]:
    archive_path, member = _find_dataset()
    with zipfile.ZipFile(archive_path) as archive:
        with archive.open(member) as stream:
            frame = pd.read_csv(stream)
    return frame, archive_path, member


def _prepare(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    if TARGET not in frame.columns:
        raise ValueError(f"Missing target column: {TARGET}")
    missing_features = EXPECTED_FEATURES.difference(frame.columns)
    if missing_features:
        raise ValueError(
            "Missing expected training feature columns: "
            + ", ".join(sorted(missing_features))
        )

    available_features = [
        column for column in frame.columns
        if column in EXPECTED_FEATURES and column not in LEAKAGE_RISK_FIELDS
    ]
    if not available_features:
        raise ValueError("No defensible candidate-side features were found.")

    for column in available_features:
        if column != "education_level":
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    target = frame[TARGET].astype(str).str.strip().str.casefold().map({"yes": 1, "no": 0})
    valid = target.notna()
    features = frame.loc[valid, available_features]
    target = target.loc[valid].astype(int)
    numeric_features = [column for column in available_features if column != "education_level"]
    categorical_features = [column for column in available_features if column == "education_level"]
    return features, target, numeric_features, categorical_features


def _build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric, numeric_features),
            ("categorical", categorical, categorical_features),
        ],
        remainder="drop",
    )


def _metrics(model: Pipeline | DummyClassifier, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, object]:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }


def _feature_distributions(frame: pd.DataFrame, features: list[str]) -> dict[str, str]:
    summaries: dict[str, str] = {}
    for feature in features:
        values = frame[feature]
        if feature == "education_level":
            counts = values.fillna("<missing>").value_counts().sort_index()
            summaries[feature] = "; ".join(
                f"{category}: {count}" for category, count in counts.items()
            )
        else:
            numeric = pd.to_numeric(values, errors="coerce")
            summaries[feature] = (
                f"numeric-like; missing={int(numeric.isna().sum())}; "
                f"min={numeric.min():g}; median={numeric.median():g}; "
                f"max={numeric.max():g}"
            )
    return summaries


def _feature_interpretation(model: Pipeline, numeric_features: list[str], categorical_features: list[str]) -> list[dict[str, object]]:
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]
    feature_names = list(preprocessor.get_feature_names_out())
    if hasattr(classifier, "coef_"):
        values = classifier.coef_[0]
    else:
        values = classifier.feature_importances_
    ranked = sorted(zip(feature_names, values), key=lambda item: abs(float(item[1])), reverse=True)
    return [
        {"feature": name, "value": round(float(value), 6)}
        for name, value in ranked[:10]
    ]


def _markdown(data: dict[str, object]) -> str:
    lines = [
        "# ML Screening Experiment",
        "",
        "This is an offline historical-label classification experiment, not the production Resume Ranking Engine.",
        "",
        "## 1. Experiment Objective",
        "",
        "Compare Logistic Regression and Random Forest for the supplied screening target `shortlisted` using defensible candidate-side features only.",
        "",
        "## 2. Dataset Used",
        "",
        f"- Archive: `{data['archive']}`\n- CSV member: `{data['member']}`\n- Rows used: {data['rows']}\n- Random seed: {SEED}",
        "",
        "## 3. Why This Dataset Was Chosen",
        "",
        "It is the only supplied dataset with a binary shortlist-like target and 30,000 structured records. The report inspection confirmed that the other datasets lack matching job/resume outcomes or are duplicated/suited for vocabulary/parser work.",
        "",
        "## 4. Why This Is Not the Production Ranking Model",
        "",
        "The dataset has no raw resume text, recruiter job requirements, or resume/job pairs. It cannot validate the application’s recruiter-specific Skills/Experience/Education/Projects score.",
        "",
        "## 5. Target Variable",
        "",
        f"`shortlisted`: Yes={data['target_distribution']['Yes']}, No={data['target_distribution']['No']}; positive rate={data['positive_rate']}%.",
        "",
        "## 6. Leakage Analysis",
        "",
        "`skills_match_score` was excluded because it is a precomputed match-like feature and can circularly encode the shortlist decision. No other direct outcome/match field was used. The dataset does not document label-generation provenance, so indirect or proxy leakage cannot be ruled out.",
        "",
        "## 7. Excluded Features",
        "",
        "- `skills_match_score`: leakage-risk precomputed matching feature.\n- `shortlisted`: target, never a feature.\n- No other source fields were available.",
        "",
        "## 8. Features Used",
        "",
        ", ".join(f"`{feature}`" for feature in data["features_used"]),
        "",
        "### Dataset distributions and live-parser compatibility",
        "",
        "| Feature | Dataset distribution | Live resume feature compatibility |",
        "|---|---|---|",
        *[
            f"| `{feature}` | {data['feature_distributions'][feature]} | "
            f"{FEATURE_COMPATIBILITY[feature]} |"
            for feature in data["features_used"]
        ],
        "",
        "These are feature-schema comparisons, not proof that the live parser produces equivalent values. "
        "`skills_match_score` is excluded as leakage risk; the target is never a feature.",
        "",
        "## 9. Data Cleaning",
        "",
        "Numeric columns were coercively parsed with invalid values becoming missing; numeric missing values use training-set medians. `education_level` is one-hot encoded with a training-fitted most-frequent imputer. The target accepts only Yes/No. "
        f"Source rows={data['source_rows']}; rows with valid labels={data['rows']}; invalid-label rows excluded={data['invalid_target_rows']}; exact duplicate rows={data['duplicate_rows']}.",
        "",
        "## 10. Train/Test Split",
        "",
        f"Stratified 80/20 split: train={data['train_rows']}, test={data['test_rows']}. Preprocessing is inside each sklearn Pipeline and is fitted only on training data.",
        "",
        "## 11. Class Distribution",
        "",
        f"Yes={data['target_distribution']['Yes']} ({data['positive_rate']}%), No={data['target_distribution']['No']} ({data['negative_rate']}%). Accuracy is therefore not sufficient by itself; precision, recall, F1, ROC-AUC, and the confusion matrix are reported.",
        "",
    ]
    baseline = data["majority_baseline"]
    lines.extend([
        "## 12. Majority-Class Baseline",
        "",
        f"Predicts the training majority class (`{data['majority_class']}`) for every test row. "
        f"Accuracy={baseline['accuracy']}, Precision={baseline['precision']}, "
        f"Recall={baseline['recall']}, F1={baseline['f1']}.",
        "",
        f"Confusion matrix `[[TN, FP], [FN, TP]]`: `{baseline['confusion_matrix']}`",
        "",
    ])
    for model_name in ("Logistic Regression", "Random Forest"):
        result = data["models"][model_name]
        lines.extend([
            f"## {13 if model_name == 'Logistic Regression' else 14}. {model_name} Results",
            "",
            f"Accuracy={result['metrics']['accuracy']}, Precision={result['metrics']['precision']}, Recall={result['metrics']['recall']}, F1={result['metrics']['f1']}, ROC-AUC={result['metrics']['roc_auc']}",
            "",
            f"Confusion matrix `[[TN, FP], [FN, TP]]`: `{result['metrics']['confusion_matrix']}`",
            "",
            "Top associated transformed features (not causal effects):",
            "",
            "\n".join(f"- `{item['feature']}`: {item['value']}" for item in result["interpretation"]),
            "",
        ])
    lines.extend([
        "## 15. Model Comparison",
        "",
        "The classifiers and majority baseline use the same held-out stratified test set. "
        "Model comparison is limited to this historical classification task; no model is promoted to production.",
        "",
        "## 16. Limitations",
        "",
        "The dataset contains engineered candidate-side features rather than resume/job pairs. "
        "Feature source definitions and units are undocumented. GitHub activity is not extracted "
        "by the live parser; resume length units and project-count semantics cannot be confirmed. "
        "It does not test recruiter-created requirements, text extraction, domain relevance, "
        "project evidence, or the production /100 score. The shortlist label may reflect an unknown historical process.",
        "",
        "## 17. Relationship to the Existing /100 Resume Ranking Engine",
        "",
        "The deterministic engine and its 40/25/20/15 weights were not modified. This experiment is isolated and does not write scores, shortlist candidates, call Flutter, or connect to Firestore/Supabase.",
        "",
        "## 18. Ranking labels needed",
        "",
        "To evaluate job-specific ranking, collect recruiter-judged relevance for each job–resume pair "
        "(for example, graded relevance levels with a documented rubric), including multiple candidates "
        "per job. Keep jobs/candidates separated between training and test. Then report NDCG@K and "
        "Precision@K (and optionally Recall@K/MAP) against those held-out judgments.",
        "",
        "## 19. Readiness",
        "",
        "Not ready for live integration: the current features cannot all be reliably reproduced from "
        "live resumes and the historical `shortlisted` label is not job-specific relevance. "
        "The experiment measures historical shortlisting classification only, not CV-ranking quality.",
        "",
    ])
    return "\n".join(lines)


def run_experiment() -> dict[str, object]:
    frame, archive, member = _load_data()
    source_rows = len(frame)
    duplicate_rows = int(frame.duplicated().sum())
    x, y, numeric_features, categorical_features = _prepare(frame)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=SEED, stratify=y
    )
    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=SEED),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, random_state=SEED, n_jobs=-1, class_weight=None
        ),
    }
    model_results: dict[str, object] = {}
    for name, classifier in models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", _build_preprocessor(numeric_features, categorical_features)),
                ("classifier", classifier),
            ]
        )
        pipeline.fit(x_train, y_train)
        model_results[name] = {
            "metrics": _metrics(pipeline, x_test, y_test),
            "interpretation": _feature_interpretation(pipeline, numeric_features, categorical_features),
        }

    majority_classifier = DummyClassifier(strategy="most_frequent")
    majority_classifier.fit(x_train, y_train)
    majority_class = int(majority_classifier.classes_[majority_classifier.class_prior_.argmax()])
    majority_metrics = _metrics(majority_classifier, x_test, y_test)
    target_distribution = {"Yes": int((y == 1).sum()), "No": int((y == 0).sum())}
    result = {
        "archive": archive.name,
        "member": member,
        "source_rows": source_rows,
        "duplicate_rows": duplicate_rows,
        "invalid_target_rows": source_rows - len(y),
        "rows": len(x),
        "features_used": list(x.columns),
        "feature_distributions": _feature_distributions(x, list(x.columns)),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "target_distribution": target_distribution,
        "majority_class": "Yes" if majority_class == 1 else "No",
        "majority_baseline": majority_metrics,
        "positive_rate": round(target_distribution["Yes"] / len(y) * 100, 3),
        "negative_rate": round(target_distribution["No"] / len(y) * 100, 3),
        "models": model_results,
    }
    REPORT_PATH.write_text(_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run_experiment()