# ai_similarity_search.py
"""
D2: AI-Powered Similar Defect Search (Offline)
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import pickle
from collections import Counter


MIN_SIMILARITY = 0.40

def similarity_band(score):
    if score >= 0.80:
        return "Very High"
    elif score >= 0.65:
        return "High"
    elif score >= 0.50:
        return "Moderate"
    else:
        return "Low"
    

ROOT_CAUSE_CLUSTER_MAP = {
    0: "Environmental / EMI & Moisture",
    1: "Maintenance / Calibration / Installation",
    2: "Environmental Aging / Material Degradation",
    3: "Mechanical / Vibration / Fasteners",
    4: "Manufacturing / Material Defect",
    5: "Design / Operational Limit Exceedance"
}
    

DATA_PATH = Path("data/analytics/defect_reports_with_clusters.csv")
MODEL_NAME = "all-MiniLM-L6-v2"
EMB_PATH = Path("data/analytics/defect_embeddings.pkl")

TEXT_COLS = ["defect_observed", "root_cause"]


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["combined_text"] = (
        df["defect_observed"].fillna("") + " " +
        df["root_cause"].fillna("")
    )
    return df


def build_embeddings(df):
    print("Loading NLP model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")
    embeddings = model.encode(
        df["combined_text"].tolist(),
        show_progress_bar=True
    )

    with open(EMB_PATH, "wb") as f:
        pickle.dump(embeddings, f)

    print(f"Embeddings saved to {EMB_PATH}")
    return embeddings, model


def load_embeddings():
    with open(EMB_PATH, "rb") as f:
        return pickle.load(f)


def find_similar(query, df, embeddings, model, top_k=5):
    query_emb = model.encode([query])
    sims = cosine_similarity(query_emb, embeddings)[0]

    top_idx = np.argsort(sims)[::-1][:top_k]

    results = []

    for idx in top_idx:
        score = float(sims[idx])

        if score < MIN_SIMILARITY:
            continue

        results.append({
            "case_id": df.iloc[idx]["case_id"],
            "system": df.iloc[idx]["system"],
            "defect": df.iloc[idx]["defect_observed"],
            "root_cause": df.iloc[idx]["root_cause"]
                if pd.notna(df.iloc[idx]["root_cause"])
                else "Not explicitly stated in report",
            "corrective_action": df.iloc[idx]["corrective_action"],
            "root_cause_cluster": df.iloc[idx]["root_cause_cluster"],
            "preventive_action": df.iloc[idx]["preventive_action"],
            "similarity_score": round(score, 3),
            "similarity_band": similarity_band(score)
    })



    return results

def generate_ai_insight(similar_cases):
    """
    Generate explainable AI insight from similar defect cases
    """
    valid_cases = [
        c for c in similar_cases
        if c.get("root_cause_cluster") is not None
    ]

    if not valid_cases:
        return None

    # Dominant root cause cluster
    clusters = [c["root_cause_cluster"] for c in valid_cases]
    dominant_cluster = Counter(clusters).most_common(1)[0][0]

    # Preventive action aggregation
    preventive_actions = [
        c["preventive_action"]
        for c in valid_cases
        if c.get("preventive_action")
    ]

    top_actions = [
        act for act, _ in Counter(preventive_actions).most_common(3)
    ]

    # Confidence score (simple & explainable)
    confidence = min(len(valid_cases) / 10, 1.0)

    return {
        "predicted_root_cause": ROOT_CAUSE_CLUSTER_MAP.get(
            dominant_cluster, "Unknown"
        ),
        "confidence": round(confidence, 2),
        "recommended_preventive_actions": top_actions
    }




def main():
    df = load_data()

    if not EMB_PATH.exists():
        embeddings, model = build_embeddings(df)
    else:
        print("Loading existing embeddings...")
        embeddings = load_embeddings()
        model = SentenceTransformer(MODEL_NAME)

    print("\nAI Similar Defect Search Ready!")
    print("Type a defect description (or 'exit'):\n")

    while True:
        query = input("🔎 Enter defect description: ").strip()

        if not query:
            print("⚠️ Please enter a valid defect description.\n")
            continue

        if query.lower() == "exit":
            break

        results = find_similar(query, df, embeddings, model)
        if not results:
            print("\n❌ No relevant defects found for the given description.\n")
            continue
        print("\nTop Similar Defects:\n")
        for r in results:
            print(f"Case ID: {r['case_id']}")
            print(f"System: {r['system']}")
            print(f"Similarity: {r['similarity_band']} ({r['similarity_score']})")
            print(f"Defect Observed: {r['defect']}")
            print(f"Root Cause: {r['root_cause']}")
            print(f"Corrective Action: {r['corrective_action']}")
            print(f"Preventive Action: {r['preventive_action']}")
            
            print("-" * 50)

        max_similarity = max(r['similarity_score'] for r in results)    
        if max_similarity >= 0.50:
            ai_insight = generate_ai_insight(results)
        else:
            ai_insight = None
            print("\nℹ️ Similar matches found, but confidence is too low to generate AI insight.\n")


        if ai_insight:
            print("\n🧠 AI Insight Summary")
            print("-------------------")
            print(f"Predicted Root Cause Category: {ai_insight['predicted_root_cause']}")
            print(f"Confidence Level: {ai_insight['confidence']}")
            print("\nRecommended Preventive Actions:")
            for act in ai_insight["recommended_preventive_actions"]:
                print(f"• {act}")


if __name__ == "__main__":
    main()
