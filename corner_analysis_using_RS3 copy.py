import pandas as pd
import streamlit as st

# Streamlit app
st.title("Telemetry Data Inspection")

# Upload the CSV file
file = st.file_uploader("Upload a CSV file", type="csv")

# Skip metadata rows and start reading telemetry data
metadata_df = pd.read_csv(file, nrows=14, header=None, engine='python')
st.write("First few rows of meta data:", metadata_df.head())
st.write("Metadata data columns:", metadata_df.columns)
telemetry_df = pd.read_csv(file)
st.write("First few rows of telemetry data:", telemetry_df.head())
st.write("Telemetry data columns:", telemetry_df.columns)
