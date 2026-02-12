"""
pages/settings.py - Trang Cài đặt
====================================
Quản lý 3 bảng mã lookup: loại KCB, cơ sở KCB, khoa
+ Quản lý Profiles hiển thị cột
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from bq_helper import get_client, run_query, get_full_table_id
from config import (
    LOOKUP_LOAIKCB_TABLE, LOOKUP_CSKCB_TABLE,
    LOOKUP_KHOA_TABLE, LOOKUP_PROFILES_TABLE,
)


# ─── All available metrics (key → display_name) ─────────────────────────────
ALL_METRIC_KEYS = [
    ("so_luot",      "Số lượt KCB"),
    ("so_ngay_dtri", "Số ngày điều trị (NT)"),
    ("t_tongchi",    "Tổng chi"),
    ("t_xn",         "Xét nghiệm"),
    ("t_cdha",       "CĐHA"),
    ("t_thuoc",      "Thuốc"),
    ("t_mau",        "Máu"),
    ("t_pttt",       "PTTT"),
    ("t_vtyt",       "VTYT"),
    ("t_kham",       "Tiền khám"),
    ("t_giuong",     "Tiền giường"),
    ("t_bhtt",       "Tiền BHTT"),
    ("t_bntt",       "Tiền BNTT"),
    ("bq_t_tongchi", "BQ Tổng chi"),
    ("bq_t_xn",      "BQ Xét nghiệm"),
    ("bq_t_cdha",    "BQ CĐHA"),
    ("bq_t_thuoc",   "BQ Thuốc"),
    ("bq_t_mau",     "BQ Máu"),
    ("bq_t_pttt",    "BQ PTTT"),
    ("bq_t_vtyt",    "BQ VTYT"),
    ("bq_t_kham",    "BQ Tiền khám"),
    ("bq_t_giuong",  "BQ Tiền giường"),
    ("bq_t_bhtt",    "BQ BHTT"),
    ("bq_t_bntt",    "BQ BNTT"),
    ("tl_thuoc_tongchi", "Tỷ lệ thuốc/tổng chi"),
    ("ngay_dttb", "Ngày ĐTTB"),
]
METRIC_DISPLAY = {k: v for k, v in ALL_METRIC_KEYS}


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
            "thu_tu": st.column_config.NumberColumn("Thứ tự", help="Thứ tự hiển thị (số nhỏ lên trước)"),
            "ma_cskcb": st.column_config.TextColumn("Mã CSKCB"),
            "makhoa_xml": st.column_config.TextColumn("Mã khoa XML"),
            "full_name": st.column_config.TextColumn("Tên đầy đủ"),
            "short_name": st.column_config.TextColumn("Tên rút gọn"),
            "valid_from": st.column_config.NumberColumn("Hiệu lực từ", help="YYYYMMDD"),
            "valid_to": st.column_config.NumberColumn("Hiệu lực đến", help="YYYYMMDD"),
        },
        "schema": [
            bigquery.SchemaField("thu_tu", "INT64"),
            bigquery.SchemaField("ma_cskcb", "STRING"),
            bigquery.SchemaField("makhoa_xml", "STRING"),
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


# ─── Profile helpers ──────────────────────────────────────────────────────────

PROFILE_SCHEMA = [
    bigquery.SchemaField("profile_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("metric_key", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("thu_tu", "INT64"),
    bigquery.SchemaField("visible", "BOOL"),
]


def _ensure_profiles_table():
    """Create lookup_profiles table if it doesn't exist."""
    client = get_client()
    full_id = get_full_table_id(LOOKUP_PROFILES_TABLE)
    table = bigquery.Table(full_id, schema=PROFILE_SCHEMA)
    client.create_table(table, exists_ok=True)


def _load_profile_names() -> list:
    """Load danh sách tên profile."""
    try:
        full_id = get_full_table_id(LOOKUP_PROFILES_TABLE)
        query = f"SELECT DISTINCT profile_name FROM `{full_id}` ORDER BY profile_name"
        df = run_query(query)
        return df["profile_name"].tolist()
    except Exception:
        return []


def _load_profile_data(profile_name: str) -> list:
    """Load metric config cho 1 profile. Returns list of dicts."""
    full_id = get_full_table_id(LOOKUP_PROFILES_TABLE)
    query = f"""
        SELECT metric_key, thu_tu, visible
        FROM `{full_id}`
        WHERE profile_name = '{profile_name}'
        ORDER BY thu_tu
    """
    df = run_query(query)
    return df.to_dict("records")


def _save_profile(profile_name: str, items: list):
    """Save profile data to BigQuery (replace all rows for this profile)."""
    _ensure_profiles_table()
    client = get_client()
    full_id = get_full_table_id(LOOKUP_PROFILES_TABLE)

    # Delete existing rows for this profile
    delete_query = f"DELETE FROM `{full_id}` WHERE profile_name = '{profile_name}'"
    client.query(delete_query).result()

    # Insert new rows
    rows = []
    for item in items:
        rows.append({
            "profile_name": profile_name,
            "metric_key": item["metric_key"],
            "thu_tu": item["thu_tu"],
            "visible": item["visible"],
        })

    if rows:
        df = pd.DataFrame(rows)
        job_config = bigquery.LoadJobConfig(
            schema=PROFILE_SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        job = client.load_table_from_dataframe(df, full_id, job_config=job_config)
        job.result()


def _delete_profile(profile_name: str):
    """Delete all rows for a profile."""
    client = get_client()
    full_id = get_full_table_id(LOOKUP_PROFILES_TABLE)
    query = f"DELETE FROM `{full_id}` WHERE profile_name = '{profile_name}'"
    client.query(query).result()


def _build_default_items() -> list:
    """Build default profile items (all visible, default order)."""
    return [
        {"metric_key": key, "thu_tu": i + 1, "visible": True}
        for i, (key, _name) in enumerate(ALL_METRIC_KEYS)
    ]


# ─── Profile Tab UI ──────────────────────────────────────────────────────────

def _render_profiles_tab():
    """Render the Profiles management tab."""

    # ── Session state init ──
    if "pf_items" not in st.session_state:
        st.session_state["pf_items"] = None
    if "pf_current" not in st.session_state:
        st.session_state["pf_current"] = None

    # ── Load profile names ──
    profile_names = _load_profile_names()

    # ── Top row: selector + create + delete ──
    col_sel, col_new, col_del = st.columns([3, 1, 1])

    with col_sel:
        options = profile_names if profile_names else []
        current_idx = 0
        if st.session_state["pf_current"] and st.session_state["pf_current"] in options:
            current_idx = options.index(st.session_state["pf_current"])

        if options:
            selected = st.selectbox(
                "Chọn profile", options, index=current_idx,
                key="pf_selector",
            )
        else:
            selected = None
            st.info("Chưa có profile nào. Hãy tạo mới.")

    with col_new:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        create_clicked = st.button("➕ Tạo mới", key="pf_create", use_container_width=True)

    with col_del:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        delete_clicked = st.button(
            "🗑️ Xóa", key="pf_delete", type="secondary",
            use_container_width=True, disabled=(selected is None),
        )

    # ── Handle Create ──
    if create_clicked:
        st.session_state["pf_show_create_dialog"] = True

    if st.session_state.get("pf_show_create_dialog"):
        with st.container(border=True):
            new_name = st.text_input("Tên profile mới:", key="pf_new_name")
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                if st.button("✅ Tạo", key="pf_confirm_create", type="primary"):
                    if new_name and new_name.strip():
                        name = new_name.strip()
                        if name in profile_names:
                            st.error(f"Profile '{name}' đã tồn tại!")
                        else:
                            items = _build_default_items()
                            _save_profile(name, items)
                            st.session_state["pf_current"] = name
                            st.session_state["pf_items"] = items
                            st.session_state["pf_show_create_dialog"] = False
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.warning("Vui lòng nhập tên profile.")
            with c2:
                if st.button("❌ Hủy", key="pf_cancel_create"):
                    st.session_state["pf_show_create_dialog"] = False
                    st.rerun()
        return  # Don't render editor while dialog is open

    # ── Handle Delete ──
    if delete_clicked and selected:
        st.session_state["pf_confirm_delete"] = selected

    if st.session_state.get("pf_confirm_delete"):
        pname = st.session_state["pf_confirm_delete"]
        st.warning(f'⚠️ Bạn có chắc muốn xóa profile **"{pname}"**?')
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if st.button("🗑️ Xác nhận xóa", key="pf_do_delete", type="primary"):
                _delete_profile(pname)
                st.session_state["pf_current"] = None
                st.session_state["pf_items"] = None
                st.session_state["pf_confirm_delete"] = None
                st.cache_data.clear()
                st.rerun()
        with c2:
            if st.button("Hủy", key="pf_cancel_delete"):
                st.session_state["pf_confirm_delete"] = None
                st.rerun()
        return

    # ── No profile selected ──
    if not selected:
        return

    # ── Load profile data if changed ──
    if st.session_state["pf_current"] != selected:
        st.session_state["pf_current"] = selected
        data = _load_profile_data(selected)
        if data:
            st.session_state["pf_items"] = data
        else:
            st.session_state["pf_items"] = _build_default_items()
        # Bump widget version to force fresh keys on profile switch
        st.session_state["pf_widget_ver"] = st.session_state.get("pf_widget_ver", 0) + 1

    items = st.session_state["pf_items"]
    if items is None:
        items = _build_default_items()
        st.session_state["pf_items"] = items

    # Deduplicate items by metric_key (keep first occurrence)
    seen_keys = set()
    deduped = []
    for it in items:
        if it["metric_key"] not in seen_keys:
            seen_keys.add(it["metric_key"])
            deduped.append(it)
    items = deduped

    # Ensure all metrics from ALL_METRIC_KEYS are present (new metrics get appended as hidden)
    existing_keys = {it["metric_key"] for it in items}
    max_thu_tu = max((it.get("thu_tu", 0) for it in items), default=0)
    for mk_key, _mk_name in ALL_METRIC_KEYS:
        if mk_key not in existing_keys:
            max_thu_tu += 1
            items.append({"metric_key": mk_key, "thu_tu": max_thu_tu, "visible": False})
    st.session_state["pf_items"] = items

    # ── Inject CSS: kill animation + match surgical-list table style ──
    st.markdown("""
    <style>
    /* Kill Streamlit transition/animation for snappier updates */
    [data-testid="stVerticalBlock"] > div,
    [data-testid="stHorizontalBlock"] > div,
    .stCheckbox, .stButton, .stMarkdown,
    [data-testid="stVerticalBlockBorderWrapper"] {
        transition: none !important;
        animation: none !important;
        animation-duration: 0s !important;
    }
    /* Zero column gaps for continuous row background */
    [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
    }
    /* Style arrow buttons as minimal blue icons (no border) */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #3b82f6 !important;
        font-size: 18px !important;
        padding: 4px 0 !important;
        min-height: 0 !important;
        line-height: 1 !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
        background: rgba(59,130,246,0.08) !important;
        border-radius: 4px !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="secondary"]:disabled {
        color: #cbd5e1 !important;
        opacity: 0.5 !important;
    }
    /* Checkbox accent color to match blue theme */
    .stCheckbox input[type="checkbox"] {
        accent-color: #3b82f6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Widget version counter: bump to force fresh widget keys ──
    if "pf_widget_ver" not in st.session_state:
        st.session_state["pf_widget_ver"] = 0
    wv = st.session_state["pf_widget_ver"]

    # ── Metric list editor ──
    visible_count = sum(1 for it in items if it['visible'])
    total_count = len(items)

    # ── Profile info line ──
    st.markdown(
        f"<div style='margin-bottom:4px;font-size:13px;color:#64748b;'>"
        f"<b style='color:#1e293b;'>Profile: {selected}</b>"
        f" · {visible_count} / {total_count} cột hiển thị</div>",
        unsafe_allow_html=True,
    )

    # ── Tri-state logic ──
    all_checked = all(it["visible"] for it in items)
    none_checked = not any(it["visible"] for it in items)
    some_checked = not all_checked and not none_checked

    # ── Header row (navy blue, rounded top) – uses same column layout as rows ──
    HDR_BG = "#2c4a7c"
    hdr_cols = st.columns([0.35, 3, 0.6, 0.25, 0.25])
    with hdr_cols[0]:
        st.markdown(
            f"<div style='text-align:center;padding:10px 0;font-weight:700;"
            f"font-size:13px;color:#fff;background:{HDR_BG};"
            f"border-radius:8px 0 0 0;letter-spacing:0.3px;"
            f"min-height:40px;line-height:20px;'>STT</div>",
            unsafe_allow_html=True,
        )
    with hdr_cols[1]:
        st.markdown(
            f"<div style='padding:10px 8px;font-weight:700;"
            f"font-size:13px;color:#fff;background:{HDR_BG};"
            f"letter-spacing:0.3px;min-height:40px;line-height:20px;'>"
            f"TÊN CHỈ TIÊU</div>",
            unsafe_allow_html=True,
        )
    with hdr_cols[2]:
        header_val = all_checked
        label_suffix = " ⬒" if some_checked else ""
        new_header = st.checkbox(
            f"Tất cả{label_suffix}", value=header_val,
            key=f"pf_hdr_v{wv}",
        )
        if new_header != header_val:
            for it in items:
                it["visible"] = new_header
            st.session_state["pf_items"] = items
            st.session_state["pf_widget_ver"] = wv + 1
            st.rerun()
    with hdr_cols[3]:
        st.markdown(
            f"<div style='text-align:center;padding:10px 0;font-weight:700;"
            f"font-size:13px;color:#fff;background:{HDR_BG};"
            f"min-height:40px;line-height:20px;'></div>",
            unsafe_allow_html=True,
        )
    with hdr_cols[4]:
        st.markdown(
            f"<div style='text-align:center;padding:10px 0;font-weight:700;"
            f"font-size:13px;color:#fff;background:{HDR_BG};"
            f"border-radius:0 8px 0 0;min-height:40px;line-height:20px;'></div>",
            unsafe_allow_html=True,
        )

    # ── Metric rows ──
    for idx, item in enumerate(items):
        key = item["metric_key"]
        display_name = METRIC_DISPLAY.get(key, key)
        visible = item.get("visible", True)

        # Clean row styling: white / very light gray alternating
        row_bg = "#ffffff" if idx % 2 == 0 else "#f8fafc"
        border_btm = "border-bottom:1px solid #e2e8f0;"

        # Text styling based on visibility
        if visible:
            txt_color = "#1e293b"
            txt_weight = "500"
            num_color = "#334155"
        else:
            txt_color = "#94a3b8"
            txt_weight = "400"
            num_color = "#cbd5e1"

        cols = st.columns([0.35, 3, 0.6, 0.25, 0.25])

        with cols[0]:
            st.markdown(
                f"<div style='text-align:center;padding:12px 0;font-size:14px;"
                f"font-weight:600;color:{num_color};background:{row_bg};"
                f"{border_btm}min-height:44px;line-height:20px;'>"
                f"{idx + 1}</div>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(
                f"<div style='padding:12px 8px;font-size:14px;"
                f"font-weight:{txt_weight};color:{txt_color};"
                f"background:{row_bg};{border_btm}"
                f"min-height:44px;line-height:20px;'>"
                f"{display_name}</div>",
                unsafe_allow_html=True,
            )
        with cols[2]:
            new_vis = st.checkbox(
                "Hiển thị", value=visible, key=f"pf_v{wv}_{key}",
                label_visibility="collapsed",
            )
            if new_vis != visible:
                st.session_state["pf_items"][idx]["visible"] = new_vis
                st.session_state["pf_widget_ver"] = wv + 1
                st.rerun()
        with cols[3]:
            if st.button("↑", key=f"pf_up{wv}_{key}", disabled=(idx == 0),
                         use_container_width=True):
                items[idx], items[idx - 1] = items[idx - 1], items[idx]
                items[idx]["thu_tu"] = idx + 1
                items[idx - 1]["thu_tu"] = idx
                st.session_state["pf_items"] = items
                st.session_state["pf_widget_ver"] = wv + 1
                st.rerun()
        with cols[4]:
            if st.button("↓", key=f"pf_dn{wv}_{key}",
                         disabled=(idx == len(items) - 1),
                         use_container_width=True):
                items[idx], items[idx + 1] = items[idx + 1], items[idx]
                items[idx]["thu_tu"] = idx + 1
                items[idx + 1]["thu_tu"] = idx + 2
                st.session_state["pf_items"] = items
                st.session_state["pf_widget_ver"] = wv + 1
                st.rerun()

    # ── Save button ──
    st.markdown("---")
    if st.button("💾 Lưu profile", key="pf_save", type="primary"):
        try:
            # Renumber thu_tu sequentially
            for i, item in enumerate(items):
                item["thu_tu"] = i + 1
            _save_profile(selected, items)
            st.success(f"✅ Đã lưu profile **{selected}** ({len(items)} chỉ tiêu)!")
            st.cache_data.clear()
            # Bump widget version to force fresh keys after save
            st.session_state["pf_widget_ver"] = st.session_state.get("pf_widget_ver", 0) + 1
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")


# ─── Main render ──────────────────────────────────────────────────────────────

def render():
    """Render trang Cài đặt."""

    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #059669, #0d9488);">
        <h1>⚙️ Cài đặt bảng mã</h1>
        <p>Quản lý bảng lookup: Loại KCB · Cơ sở KCB · Khoa · Profiles</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Tab navigation ──
    tab_names = list(TABLE_CONFIGS.keys()) + ["📊 Profiles"]
    tabs = st.tabs(tab_names)

    # Lookup table tabs
    for tab, (name, config) in zip(tabs[:len(TABLE_CONFIGS)], TABLE_CONFIGS.items()):
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

    # Profiles tab
    with tabs[-1]:
        _render_profiles_tab()
