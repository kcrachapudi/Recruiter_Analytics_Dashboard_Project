import streamlit as st
import pandas as pd

import os 
import sys

st.set_page_config(page_title="Recruiter Analytics Project", page_icon=":bar_chart:", layout="wide")
st.title("Recruiter Analytics Dashboard")

# Load Data from Local Data folder
df = pd.read_excel("../Data/recruiter_data.xlsx")