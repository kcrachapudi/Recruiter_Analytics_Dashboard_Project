import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Recruiter Analytics Dashboard", layout="wide")

st.title("📊 Recruiter Analytics Dashboard")
st.caption("Analyze hiring performance, funnel efficiency, and sourcing effectiveness")
# -------------------------------
# LOAD DATA
# -------------------------------
file_path = Path(__file__).parent / "Data" / "recruiter_analytics_dataset_raw.xlsx"
df = pd.read_excel(file_path)

# -------------------------------
# DATE CONVERSION
# -------------------------------
date_cols = ["Application_Date", "Interview_Date", "Offer_Date", "Hire_Date"]

for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# -------------------------------
# DERIVED COLUMNS (ON RAW DATA)
# -------------------------------
df["Is_Hired"] = df["Hire_Date"].notna().astype(int)
df["Is_Offered"] = df["Offer_Date"].notna().astype(int)
df["Is_Interviewed"] = df["Interview_Date"].notna().astype(int)

df["Time_to_Interview"] = (df["Interview_Date"] - df["Application_Date"]).dt.days
df["Time_to_Offer"] = (df["Offer_Date"] - df["Application_Date"]).dt.days
df["Time_to_Hire"] = (df["Hire_Date"] - df["Application_Date"]).dt.days

with st.expander("📄 View Raw Data"):
    st.dataframe(df)

st.markdown("---")

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.markdown("## 🔍 Filters")
st.sidebar.markdown("Use filters to explore hiring performance")
st.sidebar.markdown("---")

selected_source = st.sidebar.selectbox(
    "Select Source",
    options=["All"] + sorted(df["Source"].dropna().unique())
)

selected_recruiter = st.sidebar.selectbox(
    "Select Recruiter",
    options=["All"] + sorted(df["Recruiter_Name"].dropna().unique())
)
# -------------------------------
# APPLY FILTERS
# -------------------------------
df_filtered = df.copy()

if selected_source != "All":
    df_filtered = df_filtered[df_filtered["Source"] == selected_source]

if selected_recruiter != "All":
    df_filtered = df_filtered[df_filtered["Recruiter_Name"] == selected_recruiter]
# -------------------------------
# KPI CALCULATIONS
# -------------------------------
total_applications = len(df_filtered)
total_hired = df_filtered["Is_Hired"].sum()

hire_rate = total_hired / total_applications if total_applications > 0 else 0
avg_time_to_hire = df_filtered["Time_to_Hire"].dropna().mean()

# -------------------------------
# KPI DISPLAY
# -------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Total Applications", total_applications)
kpi2.metric("Total Hires", total_hired)
kpi3.metric("Hire Rate", f"{hire_rate:.2%}")
kpi4.metric(
    "Avg Time to Hire",
    f"{avg_time_to_hire:.1f} days" if pd.notna(avg_time_to_hire) else "N/A"
)

st.markdown("---")
# -------------------------------
# FUNNEL
# -------------------------------
funnel_df = pd.DataFrame({
    "Stage": ["Applied", "Interviewed", "Offered", "Hired"],
    "Count": [
        len(df_filtered),
        df_filtered["Is_Interviewed"].sum(),
        df_filtered["Is_Offered"].sum(),
        df_filtered["Is_Hired"].sum()
    ]
})

fig_funnel = px.funnel(funnel_df, x="Count", y="Stage")

st.subheader("📊 Hiring Funnel")
st.plotly_chart(fig_funnel, use_container_width=True)


with st.expander("📄 View Filtered Data"):
    st.dataframe(df_filtered)

st.markdown("---")
# -------------------------------
# SOURCE PERFORMANCE
# -------------------------------
source_perf = df_filtered.groupby("Source").agg(
    Total_Candidates=("Candidate_ID", "count"),
    Total_Hires=("Is_Hired", "sum"),
    Total_Offers=("Is_Offered", "sum"),
    Total_Interviews=("Is_Interviewed", "sum"),
    Total_Cost=("Cost_Source", "sum")
).reset_index()

source_perf["Hire_Rate"] = source_perf["Total_Hires"] / source_perf["Total_Candidates"]

source_perf["Cost_per_Hire"] = source_perf.apply(
    lambda row: round(row["Total_Cost"] / row["Total_Hires"], 0)
    if row["Total_Hires"] > 0 else None,
    axis=1
)
source_perf = source_perf.sort_values("Total_Hires", ascending=False)
# -------------------------------
# RECRUITER PERFORMANCE
# -------------------------------
recruiter_perf = df_filtered.groupby("Recruiter_Name").agg(
    Total_Candidates=("Candidate_ID", "count"),
    Total_Hires=("Is_Hired", "sum"),
    Avg_Time_to_Hire=("Time_to_Hire", "mean"),
    Avg_Time_to_Interview=("Time_to_Interview", "mean"),
    Avg_Time_to_Offer=("Time_to_Offer", "mean")
).reset_index()

recruiter_perf["Hire_Rate"] = (
    recruiter_perf["Total_Hires"] / recruiter_perf["Total_Candidates"]
)
recruiter_perf = recruiter_perf.sort_values("Total_Hires", ascending=False)
# -------------------------------
# CHARTS (SIDE BY SIDE)
# -------------------------------
col1, col2 = st.columns(2)

with col1:
    fig_source = px.bar(
        source_perf.sort_values("Total_Hires", ascending=False),
        x="Source",
        y="Total_Hires",
        title="Hires by Source"
    )
    st.plotly_chart(fig_source, use_container_width=True)
    with st.expander("📋 View Source Performance Table"):
        st.dataframe(
            source_perf.style.format({
                "Hire_Rate": "{:.1%}",
                "Cost_per_Hire": "{:.0f}"
            })
        )

with col2:
    fig_recruiter = px.bar(
        recruiter_perf.sort_values("Total_Hires", ascending=False),
        x="Recruiter_Name",
        y="Total_Hires",
        title="Hires by Recruiter"
    )
    st.plotly_chart(fig_recruiter, use_container_width=True)

    with st.expander("📋 View Recruiter Performance Table"):
        st.dataframe(
            recruiter_perf.style.format({
                "Hire_Rate": "{:.1%}",
                "Avg_Time_to_Hire": "{:.1f}",
                "Avg_Time_to_Interview": "{:.1f}",
                "Avg_Time_to_Offer": "{:.1f}"
            })
        )# -------------------------------
# TIME ANALYSIS
# -------------------------------
fig_time = px.bar(
    recruiter_perf.sort_values("Avg_Time_to_Hire"),
    x="Recruiter_Name",
    y="Avg_Time_to_Hire",
    title="Avg Time to Hire by Recruiter"
)

st.subheader("⏱️ Time to Hire by Recruiter")
st.plotly_chart(fig_time, use_container_width=True)

st.markdown("---")

# -------------------------------
# INSIGHTS SECTION
# -------------------------------
st.markdown("---")
st.subheader("📌 Key Insights")

st.markdown("""
- Referrals tend to convert at higher rates compared to other sources  
- High-volume channels may not yield the highest hiring efficiency  
- Interview stage shows the largest candidate drop-off  
- Recruiter performance varies across both speed and conversion effectiveness  
""")