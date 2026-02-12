"""
pages/settings.py - Trang Cài đặt
====================================
Quản lý 3 bảng mã lookup: loại KCB, cơ sở KCB, khoa
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from bq_helper import get_client, run_query, get_full_table_id
from config import LOOKUP_LOAIKCB_TABLE, LOOKUP_CSKCB_TABLE, LOOKUP_KHOA_TABLE


# ─── Table Configs ────────────────────────────────────────────────────────────

TABLE_CONFIGS = {
    "Loại KCB": {
        "table": LOOKUP_LOAIKCB_TABLE,
        "columns": {
            "ma_loaikcb": st.column_config.NumberColumn("Mã loại", help="Mã loại KCB (1-9)"),
            "ml2": st.column_config.TextColumn("ML2", help="Phân loại cấp 2: Nội trú / Ngoại trú"),
            "ml4": st.column_config.TextColumn("ML4", help="Phân loại cấp 4"),
            "valid_from": st.column_config.NumberColumn("Hiệu lực từ", help="YYYYMMDD"),
            "valid_to": st.column_config.NumberColumn("Hiệu lực đến", help="YYYYMMDD, để trống = không giới hạn"),
        },
        "schema": [
            bigquery.SchemaField("ma_loaikcb", "INT64"),
            bigquery.SchemaField("ml2", "STRING"),
            bigquery.SchemaField("ml4", "STRING"),
            bigquery.SchemaField("valid_from", "INT64"),
            bigquery.SchemaField("valid_to", "INT64"),
        ],
    },
    "Cơ sở KCB": {
        "table": LOOKUP_CSKCB_TABLE,
        "columns": {
            "ma_cskcb": st.column_config.TextColumn("Mã CSKCB", help="Mã cơ sở KCB"),
            "ten_cskcb": st.column_config.TextColumn("Tên CSKCB", help="Tên cơ sở khám chữa bệnh"),
            "valid_from": st.column_config.NumberColumn("Hiệu lực từ", help="YYYYMMDD"),
            "valid_to": st.column_config.NumberColumn("Hiệu lực đến", help="YYYYMMDD"),
        },
        "schema": [
            bigquery.SchemaField("ma_cskcb", "STRING"),
            bigquery.SchemaField("ten_cskcb", "STRING"),
            bigquery.SchemaField("valid_from", "INT64"),
            bigquery.SchemaField("valid_to", "INT64"),
        ],
    },
    "Khoa": {
        "table": LOOKUP_KHOA_TABLE,
        "columns": {
            "ma_cskcb": st.column_config.TextColumn("Mã CSKCB"),
            "makhoa_xml": st.column_config.TextColumn("Mã khoa XML"),
            "ma_gop": st.column_config.TextColumn("Mã gộp"),
            "full_name": st.column_config.TextColumn("Tên đầy đủ"),
            "short_name": st.column_config.TextColumn("Tên rút gọn"),
            "valid_from": st.column_config.NumberColumn("Hiệu lực từ", help="YYYYMMDD"),
            "valid_to": st.column_config.NumberColumn("Hiệu lực đến", help="YYYYMMDD"),
        },
        "schema": [
            bigquery.SchemaField("ma_cskcb", "STRING"),
            bigquery.SchemaField("makhoa_xml", "STRING"),
            bigquery.SchemaField("ma_gop", "STRING"),
            bigquery.SchemaField("full_name", "STRING"),
            bigquery.SchemaField("short_name", "STRING"),
            bigquery.SchemaField("valid_from", "INT64"),
            bigquery.SchemaField("valid_to", "INT64"),
        ],
    },
}


def _load_table(table_name: str) -> pd.DataFrame:
    """Load dữ liệu từ bảng lookup."""
    full_id = get_full_table_id(table_name)
    query = f"SELECT * FROM `{full_id}` ORDER BY 1"
    return run_query(query)


def _save_table(table_name: str, df: pd.DataFrame, schema: list):
    """Lưu DataFrame lên BigQuery (WRITE_TRUNCATE)."""
    client = get_client()
    full_id = get_full_table_id(table_name)

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_dataframe(df, full_id, job_config=job_config)
    job.result()

    table = client.get_table(full_id)
    return table.num_rows


def render():
    """Render trang Cài đặt."""

    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #059669, #0d9488);">
        <h1>⚙️ Cài đặt bảng mã</h1>
        <p>Quản lý bảng lookup: Loại KCB · Cơ sở KCB · Khoa</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Tab navigation ──
    tabs = st.tabs(list(TABLE_CONFIGS.keys()))

    for tab, (name, config) in zip(tabs, TABLE_CONFIGS.items()):
        with tab:
            table_name = config["table"]
            schema = config["schema"]
            col_config = config["columns"]

            # Load data
            data_key = f"lookup_{table_name}"
            if data_key not in st.session_state or st.session_state.get(f"{data_key}_reload"):
                st.session_state[data_key] = _load_table(table_name)
                st.session_state[f"{data_key}_reload"] = False

            df = st.session_state[data_key]

            st.markdown(f"**{name}** · `{table_name}` · {len(df)} dòng")

            # Editable table
            edited_df = st.data_editor(
                df,
                column_config=col_config,
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_{table_name}",
                hide_index=True,
            )

            # Save button
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button(f"💾 Lưu", key=f"save_{table_name}", type="primary"):
                    try:
                        num_rows = _save_table(table_name, edited_df, schema)
                        st.session_state[data_key] = edited_df
                        st.success(f"✅ Đã lưu {num_rows} dòng vào `{table_name}`!")
                        # Clear cache to reflect changes in overview
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")
            with col2:
                if st.button(f"🔄 Tải lại", key=f"reload_{table_name}"):
                    st.session_state[f"{data_key}_reload"] = True
                    st.rerun()
