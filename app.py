"""
Interactive Streamlit Dashboard
Crop Production Analysis - India, 2021 (FAOSTAT QCL)

NOTE: The source data has Production only, for one year, one country.
There is no Area harvested / Yield / multi-year data, so this dashboard is
an interactive EXPLORER of the production landscape rather than a predictor.
See README / REPORT for why the original "predict production" task could
not be built from this data, and what would be needed to add it.

Run with:
    pip install streamlit plotly pandas
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

st.set_page_config(page_title="India Crop Production Explorer", layout="wide", page_icon="🌾")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crop_production.db")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM crop_production", conn)
    conn.close()
    return df


df = load_data()

st.title("🌾 India Crop Production Explorer — 2021")
st.caption("Source: FAOSTAT (QCL domain) · Element: Production · Single snapshot year")

st.info(
    "ℹ️ This dataset contains **Production only**, for **2021 only**. "
    "It does not include Area harvested, Yield, or other years, so this "
    "dashboard is an interactive explorer rather than a prediction tool. "
    "See the report for what additional data would be needed to add forecasting.",
    icon="ℹ️",
)

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
category_sel = st.sidebar.multiselect(
    "Item Category", options=sorted(df["Item_Category"].unique()),
    default=sorted(df["Item_Category"].unique())
)
flag_sel = st.sidebar.multiselect(
    "Data Reliability", options=sorted(df["Flag_Description"].unique()),
    default=sorted(df["Flag_Description"].unique())
)
min_prod, max_prod = float(df["Production_Tonnes"].min()), float(df["Production_Tonnes"].max())
prod_range = st.sidebar.slider(
    "Production range (tonnes)", min_value=0.0, max_value=max_prod,
    value=(0.0, max_prod)
)

filtered = df[
    df["Item_Category"].isin(category_sel)
    & df["Flag_Description"].isin(flag_sel)
    & df["Production_Tonnes"].between(prod_range[0], prod_range[1])
]

st.sidebar.markdown(f"**{len(filtered)}** of {len(df)} items match your filters")

# ---------------- KPI row ----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Items shown", len(filtered))
col2.metric("Total production", f"{filtered['Production_Tonnes'].sum()/1e6:,.1f} M t")
col3.metric("Top item", filtered.loc[filtered['Production_Tonnes'].idxmax(), 'Item'] if len(filtered) else "—")
col4.metric("Median production", f"{filtered['Production_Tonnes'].median()/1e3:,.0f} K t" if len(filtered) else "—")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Rankings", "Categories", "Concentration", "Data Quality"])

with tab1:
    n = st.slider("Show top N items", 5, 50, 15)
    top_n = filtered.nlargest(n, "Production_Tonnes").sort_values("Production_Tonnes")
    fig = px.bar(top_n, x="Production_Million_Tonnes", y="Item", orientation="h",
                 color="Item_Category", title=f"Top {n} Items by Production",
                 labels={"Production_Million_Tonnes": "Production (Million Tonnes)"})
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    cat_summary = filtered.groupby("Item_Category").agg(
        total_production=("Production_Tonnes", "sum"),
        num_items=("Item", "count"),
    ).reset_index()
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(cat_summary, values="total_production", names="Item_Category",
                     title="Production Share by Category")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(cat_summary, x="Item_Category", y="num_items",
                     title="Number of Items per Category")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    sorted_df = filtered.sort_values("Production_Tonnes", ascending=False).reset_index(drop=True)
    if len(sorted_df) > 0:
        sorted_df["cum_pct"] = 100 * sorted_df["Production_Tonnes"].cumsum() / sorted_df["Production_Tonnes"].sum()
        sorted_df["rank"] = range(1, len(sorted_df) + 1)
        fig = px.line(sorted_df, x="rank", y="cum_pct", markers=True,
                       title="Cumulative % of Total Production by Item Rank",
                       labels={"rank": "Item Rank", "cum_pct": "Cumulative % of Production"})
        fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="80%")
        st.plotly_chart(fig, use_container_width=True)
        n_for_80 = (sorted_df["cum_pct"] <= 80).sum() + 1
        st.caption(f"**{n_for_80}** items account for ~80% of total production in the current filter.")

with tab4:
    flag_summary = filtered.groupby("Flag_Description").agg(
        num_items=("Item", "count"), total_production=("Production_Tonnes", "sum")
    ).reset_index()
    fig = px.bar(flag_summary, x="Flag_Description", y="total_production",
                 title="Production Volume by Data Source/Reliability",
                 labels={"total_production": "Production (Tonnes)"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(flag_summary, use_container_width=True)

st.divider()
with st.expander("View filtered raw data"):
    st.dataframe(
        filtered[["Item", "Item_Category", "Production_Tonnes", "Flag_Description", "Note"]]
        .sort_values("Production_Tonnes", ascending=False),
        use_container_width=True
    )
    st.download_button("Download filtered data as CSV", filtered.to_csv(index=False),
                        file_name="filtered_crop_production.csv")
