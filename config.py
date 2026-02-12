# config.py - Cấu hình BigQuery cho dự án CPBQ
# ================================================

# GCP Project
PROJECT_ID = "cpbq-487004"

# BigQuery Dataset & Table
DATASET_ID = "cpbq_data"
TABLE_ID = "thanh_toan_bhyt"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Lookup tables
LOOKUP_LOAIKCB_TABLE = "lookup_loaikcb"
LOOKUP_CSKCB_TABLE = "lookup_cskcb"
LOOKUP_KHOA_TABLE = "lookup_khoa"
LOOKUP_PROFILES_TABLE = "lookup_profiles"

# VIEW (enriched data)
VIEW_ID = "v_thanh_toan"

# Dataset location (asia-southeast1 = Singapore, gần Việt Nam nhất)
LOCATION = "asia-southeast1"

# Tên sheet trong file Excel
SHEET_NAME = "TH"

# Lookup file
LOOKUP_FILE = "lookup_table.xlsx"
