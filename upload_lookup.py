#!/usr/bin/env python3
"""
upload_lookup.py - Upload bảng mã lookup lên BigQuery
=====================================================
Sử dụng: source venv/bin/activate && python upload_lookup.py

Upload 3 bảng lookup từ lookup_table.xlsx:
  - loai_kcb  → lookup_loaikcb (9 rows)
  - ma_cskcb  → lookup_cskcb   (3 rows)
  - khoa      → lookup_khoa    (24 rows)

Mode: WRITE_TRUNCATE (ghi đè toàn bộ mỗi lần chạy)
"""

import os
import sys

import pandas as pd
from google.cloud import bigquery

from config import (
    PROJECT_ID, DATASET_ID, LOCATION, LOOKUP_FILE,
    LOOKUP_LOAIKCB_TABLE, LOOKUP_CSKCB_TABLE, LOOKUP_KHOA_TABLE,
)
from auth import get_credentials


# ─── Schema Definitions ──────────────────────────────────────────────────────

SCHEMAS = {
    LOOKUP_LOAIKCB_TABLE: [
        bigquery.SchemaField("ma_loaikcb", "INT64"),
        bigquery.SchemaField("ml2", "STRING"),
        bigquery.SchemaField("ml4", "STRING"),
        bigquery.SchemaField("valid_from", "INT64"),
        bigquery.SchemaField("valid_to", "INT64"),
    ],
    LOOKUP_CSKCB_TABLE: [
        bigquery.SchemaField("ma_cskcb", "STRING"),
        bigquery.SchemaField("ten_cskcb", "STRING"),
        bigquery.SchemaField("valid_from", "INT64"),
        bigquery.SchemaField("valid_to", "INT64"),
    ],
    LOOKUP_KHOA_TABLE: [
        bigquery.SchemaField("ma_cskcb", "STRING"),
        bigquery.SchemaField("makhoa_xml", "STRING"),
        bigquery.SchemaField("ma_gop", "STRING"),
        bigquery.SchemaField("full_name", "STRING"),
        bigquery.SchemaField("short_name", "STRING"),
        bigquery.SchemaField("valid_from", "INT64"),
        bigquery.SchemaField("valid_to", "INT64"),
    ],
}

# Mapping: BigQuery table name → (Excel sheet name, column rename dict)
SHEET_MAP = {
    LOOKUP_LOAIKCB_TABLE: ("loai_kcb", {"Mã loại": "ma_loaikcb"}),
    LOOKUP_CSKCB_TABLE:   ("ma_cskcb", {}),
    LOOKUP_KHOA_TABLE:    ("khoa", {}),
}


# ─── Data Transformation ─────────────────────────────────────────────────────

def prepare_dataframe(df: pd.DataFrame, table_name: str, renames: dict) -> pd.DataFrame:
    """Chuẩn hóa DataFrame cho BigQuery upload."""
    # Rename columns
    if renames:
        df = df.rename(columns=renames)

    # Cast ma_cskcb to string (match raw data schema)
    if "ma_cskcb" in df.columns:
        df["ma_cskcb"] = df["ma_cskcb"].apply(
            lambda x: str(int(x)) if pd.notna(x) else None
        )

    # Cast valid_to: NaN → None (nullable INT64)
    if "valid_to" in df.columns:
        df["valid_to"] = df["valid_to"].apply(
            lambda x: int(x) if pd.notna(x) else None
        )

    # Cast valid_from to int
    if "valid_from" in df.columns:
        df["valid_from"] = df["valid_from"].apply(
            lambda x: int(x) if pd.notna(x) else None
        )

    return df


# ─── Upload ───────────────────────────────────────────────────────────────────

def upload_table(client: bigquery.Client, df: pd.DataFrame, table_name: str):
    """Upload DataFrame lên BigQuery với WRITE_TRUNCATE."""
    full_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    schema = SCHEMAS[table_name]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"  ⏳ Uploading {len(df)} rows → {full_id}...")
    job = client.load_table_from_dataframe(df, full_id, job_config=job_config)
    job.result()

    table = client.get_table(full_id)
    print(f"  ✅ Done! {table.num_rows} rows in {table_name}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(LOOKUP_FILE):
        print(f"❌ Không tìm thấy file: {LOOKUP_FILE}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"📋 UPLOAD BẢNG MÃ LOOKUP LÊN BIGQUERY")
    print(f"{'='*60}")
    print(f"  📁 File: {LOOKUP_FILE}")
    print(f"  🎯 Dataset: {PROJECT_ID}.{DATASET_ID}")
    print()

    # Connect
    print("🔗 Kết nối BigQuery...")
    creds = get_credentials()
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION, credentials=creds)
    print(f"  ✅ Đã kết nối project '{PROJECT_ID}'")

    # Read and upload each sheet
    xls = pd.ExcelFile(LOOKUP_FILE)

    for table_name, (sheet_name, renames) in SHEET_MAP.items():
        print(f"\n📊 Sheet '{sheet_name}' → Table '{table_name}'")

        df = pd.read_excel(xls, sheet_name=sheet_name)
        print(f"  📖 Đọc được {len(df)} rows, {len(df.columns)} columns")

        df = prepare_dataframe(df, table_name, renames)
        upload_table(client, df, table_name)

    print(f"\n{'='*60}")
    print(f"🎉 HOÀN THÀNH! Đã upload {len(SHEET_MAP)} bảng lookup.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
