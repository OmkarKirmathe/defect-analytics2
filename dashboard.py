# dashboard.py
import streamlit as st
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer

from ai_similarity_search import (
    load_data as load_ai_data,
    load_embeddings,
    build_embeddings,
    find_similar,
    generate_ai_insight,
    MODEL_NAME,
    EMB_PATH
)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="AI Defect Investigation Dashboard",
    layout="wide",
    page_icon="🛡️"
)

# -------------------------------------------------
# GLOBAL STYLES (Premium Dark SaaS Theme)
# -------------------------------------------------
st.markdown("""
<style>
/* Main Background */
[data-testid="stAppViewContainer"] {
    background-color: #0f172a;
    background-image: radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.1) 0px, transparent 50%),
                      radial-gradient(at 100% 0%, rgba(236, 72, 153, 0.1) 0px, transparent 50%);
    color: #f8fafc;
}

/* Card Styling */
div.card {
    background: rgba(30, 41, 59, 0.7);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    backdrop-filter: blur(10px);
    margin-bottom: 20px;
    transition: transform 0.2s ease-in-out;
}

div.card:hover {
    border-color: rgba(255, 255, 255, 0.15);
}

/* KPI Styling */
.kpi-title {
    font-size: 0.85rem;
    font-weight: 500;
    color: #94a3b8;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    font-feature-settings: "tnum";
    font-variant-numeric: tabular-nums;
}

/* Section Headers */
.section-header {
    font-size: 1.25rem;
    font-weight: 600;
    color: #f8fafc;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}
::-webkit-scrollbar-track {
    background: #1e293b; 
}
::-webkit-scrollbar-thumb {
    background: #475569; 
    border-radius: 5px;
}
::-webkit-scrollbar-thumb:hover {
    background: #64748b; 
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
DATA_PATH = Path("data/analytics/defect_reports_with_risk.csv")

@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        st.error(f"Data file not found: {DATA_PATH}")
        return pd.DataFrame()
        
    df = pd.read_csv(DATA_PATH)

    # Ensure month column exists for timeline plot
    if "date_of_occurrence" in df.columns:
        # Convert to datetime and extract YYYY-MM
        dates = pd.to_datetime(df["date_of_occurrence"], dayfirst=True, errors="coerce")
        df["month"] = dates.dt.to_period("M").astype(str)
    else:
        df["month"] = "Unknown"

    return df

df = load_data()

@st.cache_resource
def load_ai_components():
    df_ai = load_ai_data()
    if not EMB_PATH.exists():
        embeddings, model = build_embeddings(df_ai)
    else:
        embeddings = load_embeddings()
        model = SentenceTransformer(MODEL_NAME)
    return df_ai, embeddings, model

# -------------------------------------------------
# HEADER
# -------------------------------------------------
c_head, c_logo = st.columns([4, 1])
with c_head:
    st.title("�️ AI-Powered Defect Investigation")
    st.markdown("Operational intelligence summary and semantic search for finding similar defects.")

# -------------------------------------------------
# KPI ROW
# -------------------------------------------------
# st.markdown("### 🧠 Defect Intelligence Overview")
k1, k2, k3, k4 = st.columns(4)

def kpi_card(col, title, value, icon=""):
    with col:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-title">{icon} {title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

if not df.empty:
    kpi_card(k1, "Total Defects", f"{len(df):,}", "📂")
    kpi_card(k2, "High Risk", f"{(df['risk_level']=='High').sum():,}", "⚠️")
    kpi_card(k3, "Medium Risk", f"{(df['risk_level']=='Medium').sum():,}", "🔸")
    kpi_card(k4, "Affected Systems", f"{df['system'].nunique()}", "⚙️")

# -------------------------------------------------
# PRIMARY INSIGHTS
# -------------------------------------------------
st.markdown("<div class='section-header'>📊 Operational Risk Snapshot</div>", unsafe_allow_html=True)
c1, c2 = st.columns([3, 2])

with c1:
    if not df.empty and "month" in df.columns:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        # Group by month and sort
        monthly_counts = df.groupby("month", as_index=False).size()
        monthly_counts = monthly_counts.sort_values("month")
        
        # Plot
        monthly_counts.plot(x="month", y="size", ax=ax, marker="o", color="#38bdf8", linewidth=2)
        
        # Styling to match 'Card' look (dark background for the plot area)
        fig.patch.set_facecolor('#1e293b') # Match card color
        fig.patch.set_alpha(0.7)
        ax.set_facecolor("none")
        
        ax.set_title("Defect Trends Over Time", fontsize=10, color="white", pad=15)
        ax.set_ylabel("Defect Count", color="#94a3b8")
        ax.set_xlabel("")
        ax.tick_params(axis='x', rotation=45, colors="#94a3b8")
        ax.tick_params(axis='y', colors="#94a3b8")
        ax.grid(alpha=0.1, color="white", linestyle="--")
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
            
        st.pyplot(fig)
    else:
        st.info("Insufficient data for timeline.")

with c2:
    if not df.empty:
        fig, ax = plt.subplots(figsize=(4, 3.5))
        colors = ["#22c55e", "#f59e0b", "#ef4444"] # green, orange, red
        df["risk_level"].value_counts().reindex(["Low", "Medium", "High"]).plot(
            kind="bar", ax=ax, color=colors, width=0.6
        )
        
        # Styling
        fig.patch.set_facecolor('#1e293b')
        fig.patch.set_alpha(0.7)
        ax.set_facecolor("none")
        
        ax.set_title("Risk Severity Distribution", fontsize=10, color="white", pad=15)
        ax.tick_params(colors="#94a3b8")
        ax.grid(axis="y", alpha=0.1, color="white")
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
            
        st.pyplot(fig)

# -------------------------------------------------
# SECONDARY INSIGHTS (ROW 2)
# -------------------------------------------------
st.markdown("<div class='section-header'>📊 Failure Pattern Insights</div>", unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)

with s1:
    if not df.empty:
        fig, ax = plt.subplots(figsize=(4,3))
        df["system"].value_counts().head(8).plot(kind="barh", ax=ax, color="#38bdf8")
        
        # Styling
        fig.patch.set_facecolor('#1e293b')
        fig.patch.set_alpha(0.7)
        ax.set_facecolor("none")
        
        ax.set_title("Top Failing Systems", fontsize=9, color="white")
        ax.tick_params(colors="#94a3b8")
        ax.grid(axis="x", alpha=0.1, color="white")
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
            
        st.pyplot(fig)

with s2:
    if not df.empty:
        fig, ax = plt.subplots(figsize=(4,3))
        df["defect_category"].value_counts().plot(kind="bar", ax=ax, color="#a78bfa")
        
        # Styling
        fig.patch.set_facecolor('#1e293b')
        fig.patch.set_alpha(0.7)
        ax.set_facecolor("none")
        
        ax.set_title("Defect Categories", fontsize=9, color="white")
        ax.tick_params(colors="#94a3b8")
        ax.grid(axis="y", alpha=0.1, color="white")
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
            
        st.pyplot(fig)

with s3:
    if not df.empty:
        fig, ax = plt.subplots(figsize=(4,3))
        df["root_cause_cluster"].value_counts().sort_index().plot(kind="bar", ax=ax, color="#f472b6")
        
        # Styling
        fig.patch.set_facecolor('#1e293b')
        fig.patch.set_alpha(0.7)
        ax.set_facecolor("none")
        
        ax.set_title("Root Cause Clusters", fontsize=9, color="white")
        ax.tick_params(colors="#94a3b8")
        ax.grid(axis="y", alpha=0.1, color="white")
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
            
        st.pyplot(fig)

# -------------------------------------------------
# DEEP-DIVE (EXPANDERS)
# -------------------------------------------------
with st.expander("🔍 Reliability & Maintenance Deep-Dive"):
    d1, d2 = st.columns(2)

    with d1:
        if not df.empty:
            fig, ax = plt.subplots(figsize=(5,3))
            df.groupby("system")["life_hours"].mean().sort_values().tail(8).plot(
                kind="barh", ax=ax, color="#22d3ee"
            )
            
            # Styling
            fig.patch.set_facecolor('#1e293b')
            fig.patch.set_alpha(0.7)
            ax.set_facecolor("none")
            
            ax.set_title("Mean Life Before Failure (Hours)", fontsize=9, color="white")
            ax.tick_params(colors="#94a3b8")
            ax.grid(axis="x", alpha=0.1, color="white")
            
            for spine in ax.spines.values():
                spine.set_color('#334155')
                
            st.pyplot(fig)

    with d2:
        if not df.empty:
            fig, ax = plt.subplots(figsize=(5,3))
            df["trade"].value_counts().plot(kind="pie", ax=ax, autopct="%1.1f%%", 
                colors=["#38bdf8", "#818cf8", "#c084fc", "#f472b6"])
            
            # Styling
            fig.patch.set_facecolor('#1e293b')
            fig.patch.set_alpha(0.7)
            ax.set_facecolor("none")
            
            ax.set_title("Defects by Trade", fontsize=9, color="white")
            ax.set_ylabel("")
            plt.setp(ax.texts, color="white")
            
            st.pyplot(fig)

# -------------------------------------------------
# DATA INSPECTOR (PREVIEW)
# -------------------------------------------------
with st.expander("🔎 Data Inspector & Previous Previews (Raw Data)", expanded=False):
    st.markdown("Explore the underlying dataset used for these metrics.")
    st.dataframe(df, use_container_width=True)

# -------------------------------------------------
# AI SIMILARITY SEARCH
# -------------------------------------------------
st.markdown("<div class='section-header'>🤖 AI Similar Defect Search</div>", unsafe_allow_html=True)

# Session state for example query
# Session state for example query
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""

def set_example():
    st.session_state["search_query"] = "Landing gear hydraulic fluid leak observed during pre-flight check."

col_search, col_btn = st.columns([5, 1])
with col_btn:
    st.write("") # Spacer
    st.write("") 
    # Use on_click to ensure state updates before render
    st.button("🎲 Example", on_click=set_example)

with col_search:
    query = st.text_area(
        "Describe the defect to find similar historical cases:", 
        key="search_query",
        height=100,
        placeholder="e.g. 'Cracks found in the fuselage near the wing root...'"
    )

if st.button("Find Similar Defects", type="primary"):
    if not query:
        st.warning("Please enter a description.")
    else:
        with st.spinner("Searching vector database..."):
            df_ai, embeddings, model = load_ai_components()
            results = find_similar(query, df_ai, embeddings, model)

        if results:
            st.markdown(f"### Found {len(results)} Similar Cases")
            for r in results:
                # Similarity strength badge color
                band_color = {
                    "Very High": "green",
                    "High": "orange",
                    "Moderate": "yellow",
                    "Low": "grey"
                }.get(r.get("similarity_band", "Low"), "grey")
                
                with st.expander(f"Case {r['case_id']} | {r['system']} | Score: {r['similarity_score']}"):
                    c_det1, c_det2 = st.columns(2)
                    with c_det1:
                        st.markdown(f"**Defect Observed:**\n{r['defect']}")
                        st.markdown(f"**Root Cause:**\n{r['root_cause']}")
                    with c_det2:
                        st.markdown(f"**Corrective Action:**\n{r['corrective_action']}")
                        st.markdown(f"**Preventive Action:**\n{r['preventive_action']}")
                        st.caption(f"Similarity Band: :{band_color}[{r['similarity_band']}]")

            ai = generate_ai_insight(results)
            if ai:
                st.markdown("### 🧠 AI Insight Summary")
                st.info(f"**Predicted Root Cause:** {ai['predicted_root_cause']} (Confidence: {ai['confidence']})")
                st.markdown("**Recommended Preventive Strategies:**")
                for a in ai["recommended_preventive_actions"]:
                    st.markdown(f"- {a}")
        else:
            st.info("No similar defects found.")
