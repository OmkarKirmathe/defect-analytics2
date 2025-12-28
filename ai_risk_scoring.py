# ai_risk_scoring.py
"""
D4: Risk Scoring / Severity Prediction (Offline, Explainable)
"""

import pandas as pd
from pathlib import Path
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

DATA_PATH = Path("data/analytics/defect_reports_with_clusters.csv")
OUT_PATH = Path("data/analytics/defect_reports_with_risk.csv")


def load_data():
    df = pd.read_csv(DATA_PATH)

    # Basic cleaning
    df["life_hours"] = pd.to_numeric(df["life_hours"], errors="coerce").fillna(df["life_hours"].median())
    df["defect_len"] = df["defect_observed"].astype(str).str.len()

    # Target label (heuristic, explainable)
    # Mission Critical / Critical → High risk
    df["risk_label"] = df["defect_category"].apply(
        lambda x: 1 if str(x).lower() in ["mission critical", "critical"] else 0
    )

    return df


def build_model(df):
    features_num = ["life_hours", "defect_len", "root_cause_cluster"]
    features_cat = ["system"]

    X = df[features_num + features_cat]
    y = df["risk_label"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", features_num),
            ("cat", OneHotEncoder(handle_unknown="ignore"), features_cat),
        ]
    )

    model = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("clf", LogisticRegression(max_iter=1000))
        ]
    )

    return model, X, y


def main():
    df = load_data()
    model, X, y = build_model(df)

    # Train (offline, historical)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model.fit(X_train, y_train)

    # Predict risk probability
    df["risk_score"] = model.predict_proba(X)[:, 1]

    # Convert to human-readable level
    def risk_level(score):
        if score >= 0.7:
            return "High"
        elif score >= 0.4:
            return "Medium"
        else:
            return "Low"

    df["risk_level"] = df["risk_score"].apply(risk_level)

    df.to_csv(OUT_PATH, index=False)

    print("✅ Risk scoring completed")
    print(f"Output saved to: {OUT_PATH}")
    print("\nRisk Level Distribution:")
    print(df["risk_level"].value_counts())


if __name__ == "__main__":
    main()
