"""BigQuery connection helper for Streamlit app."""

import streamlit as st
from google.cloud import bigquery
from auth import get_credentials
from config import PROJECT_ID, DATASET_ID, LOCATION


@st.cache_resource
def get_client() -> bigquery.Client:
    """Tạo BigQuery client (cached)."""
    creds = get_credentials()
    return bigquery.Client(project=PROJECT_ID, location=LOCATION, credentials=creds)


def run_query(query: str):
    """Chạy query và trả về DataFrame."""
    client = get_client()
    return client.query(query).to_dataframe()


def get_full_table_id(table_name: str) -> str:
    """Trả về full table ID."""
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
