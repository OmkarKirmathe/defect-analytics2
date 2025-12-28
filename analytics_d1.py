# analytics_d1.py
"""
STEP D1: Core Analytics for Defect Investigation Data
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_PATH = Path("data/analytics/defect_reports.csv")
OUT_DIR = Path("data/analytics/plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} defect records")
    return df


def preprocess(df):
    # Parse dates safely
    for col in ["date_of_occurrence", "date_component_received"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # Ensure numeric life
    df["life_hours"] = pd.to_numeric(df.get("life_hours"), errors="coerce")

    return df


def defects_over_time(df):
    df_time = df.dropna(subset=["date_of_occurrence"])
    trend = df_time.groupby(df_time["date_of_occurrence"].dt.to_period("M")).size()

    trend.plot(kind="line", marker="o")
    plt.title("Defects Over Time (Monthly)")
    plt.xlabel("Month")
    plt.ylabel("Number of Defects")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "defects_over_time.png")
    plt.clf()


def top_failing_systems(df, top_n=10):
    sys_counts = df["system"].value_counts().head(top_n)

    sys_counts.plot(kind="bar")
    plt.title("Top Failing Systems")
    plt.xlabel("System")
    plt.ylabel("Defect Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "top_failing_systems.png")
    plt.clf()


def defects_by_trade(df):
    trade_counts = df["trade"].value_counts()

    trade_counts.plot(kind="pie", autopct="%1.1f%%")
    plt.title("Defects by Trade")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "defects_by_trade.png")
    plt.clf()


def mean_life_before_failure(df):
    life_df = df.dropna(subset=["life_hours"])

    mean_life = life_df.groupby("system")["life_hours"].mean().sort_values(ascending=False)

    mean_life.head(10).plot(kind="bar")
    plt.title("Mean Life Before Failure (Top Systems)")
    plt.xlabel("System")
    plt.ylabel("Life (Hours)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "mean_life_before_failure.png")
    plt.clf()


def defect_category_distribution(df):
    cat_counts = df["defect_category"].value_counts()

    cat_counts.plot(kind="bar")
    plt.title("Defect Category Distribution")
    plt.xlabel("Category")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "defect_category_distribution.png")
    plt.clf()


def corrective_vs_preventive(df):
    df["corrective_len"] = df["corrective_action"].astype(str).str.len()
    df["preventive_len"] = df["preventive_action"].astype(str).str.len()

    df[["corrective_len", "preventive_len"]].mean().plot(kind="bar")
    plt.title("Average Length: Corrective vs Preventive Actions")
    plt.ylabel("Characters (proxy for complexity)")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "corrective_vs_preventive.png")
    plt.clf()


def main():
    df = load_data()
    df = preprocess(df)

    defects_over_time(df)
    top_failing_systems(df)
    defects_by_trade(df)
    mean_life_before_failure(df)
    defect_category_distribution(df)
    corrective_vs_preventive(df)

    print("\n✅ STEP D1 Analytics completed.")
    print(f"Plots saved in: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
