import os 
import sys

import streamlit as st
import pandas as pd

import plotly.express as px

st.set_page_config(page_title="Recruiter Analytics Project", page_icon=":bar_chart:", layout="wide")
st.title("Recruiter Analytics Dashboard")

# Load Data from Local Data folder
df = pd.read_excel("../Data/recruiter_analytics_dataset_raw.xlsx")

# Show Preview of the Data
st.subheader("Data Preview")
st.dataframe(df.head())

# Fix Date Columns
date_cols = ["Application_Date", "Interview_Date", "Offer_Date", "Hire_Date"]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# KPIs Section
total_applications = len(df)

###############################################
# Sidebar Filters
st.sidebar.header("🔍 Filters")
# Source Sidebar filter
selected_sources = st.sidebar.multiselect(
    "Select Source",
    options=df["Source"].unique(),
    default=df["Source"].unique()
)
# Recruiter Sidebar filters
selected_recruiters = st.sidebar.multiselect(
    "Select Recruiter",
    options=df["Recruiter_Name"].unique(),
    default=df["Recruiter_Name"].unique()
)
###############################################

# Total Hired based on Hire Date
total_hired = df["Hire_Date"].notna().sum()

#Hire Rate
hire_rate = total_hired / total_applications if total_applications > 0 else 0
if hire_rate > 0:
    hire_rate_percentage = f"{hire_rate:.2%}"
else:
    hire_rate_percentage = "N/A"

# Time to Hire
df["Time_to_Hire"] = (df["Hire_Date"] - df["Application_Date"]).dt.days

# Average Time to Hire
avg_time_to_hire = df["Time_to_Hire"].dropna().mean()


col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Applications", total_applications)
col2.metric("Total Hires", total_hired)
col3.metric("Hire Rate", f"{hire_rate:.2%}")
col4.metric("Avg Time to Hire", f"{avg_time_to_hire:.1f} days")

# Build Flags
df["Is_Hired"] = df["Hire_Date"].notna().astype(int)
df["Is_Offered"] = df["Offer_Date"].notna().astype(int)
df["Is_Interviewed"] = df["Interview_Date"].notna().astype(int)

source_perf = df.groupby("Source").agg(
    Total_Candidates=("Candidate_ID", "count"),
    Total_Hires=("Is_Hired", "sum"),
    Total_Offers=("Is_Offered", "sum"),
    Total_Interviews=("Is_Interviewed", "sum"),
    Total_Cost=("Cost_Source", "sum")
).reset_index()

source_perf["Hire_Rate"] = source_perf["Total_Hires"] / source_perf["Total_Candidates"]
source_perf["Hire_Rate_Percent"] = source_perf["Hire_Rate"] * 100
source_perf["Cost_per_Hire"] = source_perf.apply(
    lambda row: round(row["Total_Cost"] / row["Total_Hires"], 0)
    if row["Total_Hires"] > 0 else None,
    axis=1
)
st.subheader("📊 Source Performance")
st.dataframe(source_perf)

# Recruiter Performance
recruiter_perf = df.groupby("Recruiter_Name").agg(
    Total_Candidates=("Candidate_ID", "count"),
    Total_Hires=("Is_Hired", "sum"),
    Total_Offers=("Is_Offered", "sum"),
    Total_Interviews=("Is_Interviewed", "sum")
).reset_index()

recruiter_perf["Hire_Rate"] = (
    recruiter_perf["Total_Hires"] / recruiter_perf["Total_Candidates"]
)

recruiter_perf["Submissions_per_Hire"] = recruiter_perf.apply(
    lambda row: row["Total_Candidates"] / row["Total_Hires"]
    if row["Total_Hires"] > 0 else None,
    axis=1
)

#Recruiter Time Analysis
recruiter_time = df.groupby("Recruiter_Name").agg(
    Avg_Time_to_Hire=("Time_to_Hire", "mean"),
    Avg_Time_to_Interview=("Interview_Date", lambda x: (x - df.loc[x.index, "Application_Date"]).dt.days.mean()),
    Avg_Time_to_Offer=("Offer_Date", lambda x: (x - df.loc[x.index, "Application_Date"]).dt.days.mean())
).reset_index()
# Merge Recruiter Time Analysis with Recruiter Performance
recruiter_perf = recruiter_perf.merge(recruiter_time, on="Recruiter_Name", how="left")

st.subheader("👩‍💼 Recruiter Performance")
st.dataframe(recruiter_perf)

# Create Time Columns
# Time calculations
df["Time_to_Interview"] = (df["Interview_Date"] - df["Application_Date"]).dt.days
df["Time_to_Offer"] = (df["Offer_Date"] - df["Application_Date"]).dt.days
df["Time_to_Hire"] = (df["Hire_Date"] - df["Application_Date"]).dt.days

# Time KPIs
avg_tti = df["Time_to_Interview"].dropna().mean()
avg_tto = df["Time_to_Offer"].dropna().mean()
avg_tth = df["Time_to_Hire"].dropna().mean()

st.subheader("⏱️ Time Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Avg Time to Interview", f"{avg_tti:.1f} days")
col2.metric("Avg Time to Offer", f"{avg_tto:.1f} days")
col3.metric("Avg Time to Hire", f"{avg_tth:.1f} days")

# Time by Source
time_by_source = df.groupby("Source").agg(
    Avg_Time_to_Hire=("Time_to_Hire", "mean"),
    Avg_Time_to_Interview=("Time_to_Interview", "mean"),
    Avg_Time_to_Offer=("Time_to_Offer", "mean")
).reset_index()

st.subheader("⏱️ Time by Source")
st.dataframe(time_by_source)

# Time by Recruiter
time_by_recruiter = df.groupby("Recruiter_Name").agg(
    Avg_Time_to_Hire=("Time_to_Hire", "mean"),
    Avg_Time_to_Interview=("Time_to_Interview", "mean"),
    Avg_Time_to_Offer=("Time_to_Offer", "mean")
).reset_index()

st.subheader("⏱️ Time by Recruiter")
st.dataframe(time_by_recruiter)

# Hiring Funnel Analysis
funnel_data = {
    "Stage": ["Applied", "Interviewed", "Offered", "Hired"],
    "Count": [
        len(df),
        df["Interview_Date"].notna().sum(),
        df["Offer_Date"].notna().sum(),
        df["Hire_Date"].notna().sum()
    ]
}
funnel_df = pd.DataFrame(funnel_data)

# Plot Funnel Chart

fig_funnel = px.funnel(
    funnel_df,
    x="Count",
    y="Stage"
)

st.subheader("📊 Hiring Funnel")
st.plotly_chart(fig_funnel, use_container_width=True)

# Source Performance Plot
fig_source = px.bar(
    source_perf,
    x="Source",
    y="Total_Hires",
    title="Hires by Source"
)

st.subheader("📊 Source Performance")
st.plotly_chart(fig_source, use_container_width=True)

fig_source2 = px.bar(
    source_perf.sort_values("Total_Hires", ascending=False),
    x="Source",
    y="Total_Hires",
    title="Hires by Source"
)
st.subheader("📊 Source Performance Descending")
st.plotly_chart(fig_source2, use_container_width=True)

# Recruiter Performance Plot
fig_recruiter = px.bar(
    recruiter_perf.sort_values("Total_Hires", ascending=False),
    x="Recruiter_Name",
    y="Total_Hires",
    title="Hires by Recruiter"
)

st.subheader("📊 Recruiter Performance")
st.plotly_chart(fig_recruiter, use_container_width=True)

# Recruiter Time to Hire Plot
fig_time = px.bar(
    recruiter_perf,
    x="Recruiter_Name",
    y="Avg_Time_to_Hire",
    title="Avg Time to Hire by Recruiter"
)

st.subheader("⏱️ Time to Hire by Recruiter")
st.plotly_chart(fig_time, use_container_width=True)

