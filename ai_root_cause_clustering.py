# ai_root_cause_clustering.py
"""
D3: Root Cause Clustering (Unsupervised AI)
"""

import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

DATA_PATH = "data/analytics/defect_reports_with_clusters.csv"
OUT_PATH = Path("data/analytics/defect_reports_with_clusters.csv")

NUM_CLUSTERS = 6   # you can tune this (5–8 recommended)


def load_data():
    df = pd.read_csv(DATA_PATH)

    # Handle missing root cause
    df["root_cause_clean"] = df["root_cause"].fillna("Not specified")

    return df


def vectorize_text(text_series):
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words="english"
    )
    X = vectorizer.fit_transform(text_series)
    return X, vectorizer


def cluster_text(X):
    model = KMeans(
        n_clusters=NUM_CLUSTERS,
        random_state=42,
        n_init=10
    )
    labels = model.fit_predict(X)
    return labels, model


def print_cluster_keywords(model, vectorizer):
    terms = vectorizer.get_feature_names_out()

    print("\n🔹 Root Cause Clusters & Top Keywords:\n")
    for i in range(NUM_CLUSTERS):
        top_indices = model.cluster_centers_[i].argsort()[-10:][::-1]
        keywords = [terms[j] for j in top_indices]
        print(f"Cluster {i}: {', '.join(keywords)}")


def main():
    df = load_data()
    X, vectorizer = vectorize_text(df["root_cause_clean"])
    labels, model = cluster_text(X)

    df["root_cause_cluster"] = labels

    df.to_csv(OUT_PATH, index=False)

    print(f"\n✅ Clustering completed")
    print(f"Clusters saved to: {OUT_PATH}")
    print_cluster_keywords(model, vectorizer)


if __name__ == "__main__":
    main()
