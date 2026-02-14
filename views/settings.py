"""
pages/settings.py - Trang Cài đặt
====================================
Quản lý 3 bảng mã lookup: loại KCB, cơ sở KCB, khoa
+ Quản lý Profiles hiển thị cột
+ Quản lý Gộp khoa
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from bq_helper import get_client, run_query, get_full_table_id
from config import (
    LOOKUP_LOAIKCB_TABLE, LOOKUP_CSKCB_TABLE,
    LOOKUP_KHOA_TABLE, LOOKUP_PROFILES_TABLE,
    LOOKUP_KHOA_MERGE_TABLE,
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
DEFAULT_ORDER = {k: i for i, (k, _) in enumerate(ALL_METRIC_KEYS)}


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

    # Ensure every item has a stable default_order for unchecked sorting
    for it in items:
        if "default_order" not in it:
            it["default_order"] = DEFAULT_ORDER.get(it["metric_key"], 999)
    st.session_state["pf_items"] = items

    # ── Inject CSS for profile table UI ──
    st.markdown("""
    <style>
    /* Kill Streamlit transition/animation */
    [data-testid="stVerticalBlock"] > div,
    [data-testid="stHorizontalBlock"] > div,
    .stCheckbox, .stButton, .stMarkdown,
    [data-testid="stVerticalBlockBorderWrapper"] {
        transition: none !important;
        animation: none !important;
        animation-duration: 0s !important;
    }
    /* Tight column alignment */
    [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
        align-items: center !important;
    }
    /* Compact checkbox label */
    .stCheckbox > label { margin-bottom: 0 !important; }
    .stCheckbox > label > span { font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Widget version counter ──
    if "pf_widget_ver" not in st.session_state:
        st.session_state["pf_widget_ver"] = 0
    wv = st.session_state["pf_widget_ver"]

    visible_count = sum(1 for it in items if it['visible'])
    total_count = len(items)
    all_checked = all(it["visible"] for it in items)

    # ── Header: Profile name + count + "Chọn tất cả" toggle ──
    hdr_left, hdr_right = st.columns([4, 1])
    with hdr_left:
        st.markdown(
            f"<div style='margin-bottom:2px;'>"
            f"<span style='font-size:18px;font-weight:700;color:#1e293b;'>"
            f"Profile: {selected}</span></div>"
            f"<div style='font-size:13px;color:#64748b;margin-bottom:8px;'>"
            f"Đã chọn <b>{visible_count}</b> / {total_count} chỉ tiêu hiển thị</div>",
            unsafe_allow_html=True,
        )
    with hdr_right:
        toggle_key = f"pf_hdr_v{wv}"

        # When an individual checkbox changed, we must reset the toggle
        # so it reflects the new computed all_checked value
        if st.session_state.get("pf_toggle_dirty"):
            st.session_state["pf_toggle_dirty"] = False
            if toggle_key in st.session_state:
                del st.session_state[toggle_key]

        def _on_toggle_all():
            val = st.session_state[toggle_key]
            for it in st.session_state["pf_items"]:
                it["visible"] = val
            # Bump widget version so checkboxes get fresh keys
            st.session_state["pf_widget_ver"] = \
                st.session_state.get("pf_widget_ver", 0) + 1

        st.toggle(
            "Chọn tất cả", value=all_checked,
            key=toggle_key, on_change=_on_toggle_all,
        )

    # ── Table header (blue gradient) ──
    st.markdown(
        "<div style='display:flex;align-items:center;padding:10px 16px;"
        "background:linear-gradient(135deg,#1e3a8a,#2563eb);"
        "border-radius:8px 8px 0 0;color:#fff;"
        "font-size:12px;font-weight:600;letter-spacing:0.8px;"
        "text-transform:uppercase;'>"
        "<span style='width:50px;text-align:center;'>STT</span>"
        "<span style='flex:1;padding-left:12px;'>Tên chỉ tiêu</span>"
        "<span style='width:80px;text-align:center;'>Thao tác</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Build display list: checked first, then unchecked ──
    checked = [it for it in items if it.get("visible", True)]
    unchecked = [it for it in items if not it.get("visible", True)]
    checked.sort(key=lambda x: x.get("thu_tu", 0))
    unchecked.sort(key=lambda x: x.get("default_order", 999))
    display_items = checked + unchecked

    # ── Scrollable row list ──
    with st.container(height=480):
        ck_stt = 0   # STT counter for checked group
        uc_stt = 0   # STT counter for unchecked group

        for item in display_items:
            key = item["metric_key"]
            display_name = METRIC_DISPLAY.get(key, key)
            visible = item.get("visible", True)
            # Find real index in items list (for callbacks)
            real_idx = next(i for i, it in enumerate(items)
                           if it["metric_key"] == key)

            if visible:
                ck_stt += 1
                stt_num = ck_stt
                # Checked row styling: blue tint alternating
                nc = "#2563eb"
                nw = "700"
            else:
                uc_stt += 1
                stt_num = uc_stt
                # Unchecked row styling: neutral
                nc = "#94a3b8"
                nw = "400"

            # Columns: STT | Checkbox+Name | (↑ | ↓) or empty
            if visible:
                cols = st.columns([0.35, 5.3, 0.18, 0.18])
            else:
                cols = st.columns([0.35, 5.65])

            with cols[0]:
                st.markdown(
                    f"<div style='font-size:14px;font-weight:{nw};"
                    f"color:{nc};text-align:center;padding:6px 0;'>"
                    f"{stt_num}</div>",
                    unsafe_allow_html=True,
                )

            with cols[1]:
                cb_key = f"pf_v{wv}_{key}"

                def _on_cb(_ridx=real_idx, _key=cb_key):
                    new_val = st.session_state[_key]
                    st.session_state["pf_items"][_ridx]["visible"] = new_val
                    if new_val:
                        # Checked → place at end of checked group
                        max_tt = max(
                            (it.get("thu_tu", 0)
                             for it in st.session_state["pf_items"]
                             if it["visible"]),
                            default=0,
                        )
                        st.session_state["pf_items"][_ridx]["thu_tu"] = \
                            max_tt + 1
                    st.session_state["pf_toggle_dirty"] = True

                st.checkbox(
                    display_name, value=visible,
                    key=cb_key, on_change=_on_cb,
                )

            # ↑↓ only for checked rows
            if visible:
                ck_idx_in_checked = ck_stt - 1  # 0-based position in checked
                with cols[2]:
                    if st.button("↑", key=f"pf_up{wv}_{key}",
                                 disabled=(ck_idx_in_checked == 0)):
                        # Swap with prev in checked list
                        prev_item = checked[ck_idx_in_checked - 1]
                        cur_tt = item["thu_tu"]
                        item["thu_tu"] = prev_item["thu_tu"]
                        prev_item["thu_tu"] = cur_tt
                        st.session_state["pf_items"] = items
                        st.session_state["pf_widget_ver"] = wv + 1
                        st.rerun()

                with cols[3]:
                    if st.button("↓", key=f"pf_dn{wv}_{key}",
                                 disabled=(
                                     ck_idx_in_checked >= len(checked) - 1
                                 )):
                        next_item = checked[ck_idx_in_checked + 1]
                        cur_tt = item["thu_tu"]
                        item["thu_tu"] = next_item["thu_tu"]
                        next_item["thu_tu"] = cur_tt
                        st.session_state["pf_items"] = items
                        st.session_state["pf_widget_ver"] = wv + 1
                        st.rerun()

            # Row divider
            st.markdown(
                "<div style='border-bottom:1px solid #d9dfe8;'></div>",
                unsafe_allow_html=True,
            )

    # ── Footer: Cancel + Save ──
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    ft_left, ft_mid, ft_cancel, ft_save = st.columns([3, 1, 1, 1.2])
    with ft_left:
        st.markdown(
            "<div style='font-size:12px;color:#94a3b8;padding-top:8px;'>"
            "</div>",
            unsafe_allow_html=True,
        )
    with ft_cancel:
        if st.button("Hủy bỏ", key="pf_cancel", use_container_width=True):
            # Reload original data
            data = _load_profile_data(selected)
            if data:
                st.session_state["pf_items"] = data
            else:
                st.session_state["pf_items"] = _build_default_items()
            st.session_state["pf_widget_ver"] = wv + 1
            st.cache_data.clear()
            st.rerun()
    with ft_save:
        if st.button("💾 Lưu profile", key="pf_save", type="primary",
                      use_container_width=True):
            try:
                with st.spinner("⏳ Đang lưu profile..."):
                    # Sort in display order (checked by thu_tu,
                    # unchecked by default_order) before saving
                    ck = [it for it in items if it.get("visible", True)]
                    uc = [it for it in items if not it.get("visible", True)]
                    ck.sort(key=lambda x: x.get("thu_tu", 0))
                    uc.sort(key=lambda x: x.get("default_order", 999))
                    ordered = ck + uc
                    for i, item in enumerate(ordered):
                        item["thu_tu"] = i + 1
                    _save_profile(selected, ordered)
                    st.cache_data.clear()
                    st.session_state["pf_widget_ver"] = wv + 1
                st.success(f"✅ Đã lưu profile **{selected}** ({len(items)} chỉ tiêu)!")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")


# ─── Merge Khoa helpers ──────────────────────────────────────────────────────

MERGE_SCHEMA = [
    bigquery.SchemaField("target_khoa", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("source_khoa", "STRING", mode="REQUIRED"),
]


def _ensure_merge_table():
    """Create lookup_khoa_merge table if it doesn't exist."""
    client = get_client()
    full_id = get_full_table_id(LOOKUP_KHOA_MERGE_TABLE)
    table = bigquery.Table(full_id, schema=MERGE_SCHEMA)
    client.create_table(table, exists_ok=True)


def _load_merge_groups() -> list:
    """Load merge rules grouped by target_khoa.
    Returns list of dicts: [{target_khoa, sources: [source1, source2, ...]}]
    """
    try:
        full_id = get_full_table_id(LOOKUP_KHOA_MERGE_TABLE)
        query = f"SELECT target_khoa, source_khoa FROM `{full_id}` ORDER BY target_khoa, source_khoa"
        df = run_query(query)
        if df is None or df.empty:
            return []
        groups = {}
        for _, row in df.iterrows():
            target = row["target_khoa"]
            if target not in groups:
                groups[target] = []
            groups[target].append(row["source_khoa"])
        return [{"target_khoa": t, "sources": srcs} for t, srcs in groups.items()]
    except Exception:
        return []


def _save_merge_groups(groups: list):
    """Save all merge groups to BigQuery (WRITE_TRUNCATE)."""
    _ensure_merge_table()
    client = get_client()
    full_id = get_full_table_id(LOOKUP_KHOA_MERGE_TABLE)

    rows = []
    for g in groups:
        for src in g["sources"]:
            rows.append({"target_khoa": g["target_khoa"], "source_khoa": src})

    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=["target_khoa", "source_khoa"])

    job_config = bigquery.LoadJobConfig(
        schema=MERGE_SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_dataframe(df, full_id, job_config=job_config)
    job.result()


def _load_khoa_options() -> list:
    """Load all khoa entries for dropdown display.
    Returns list of dicts: {short_name, makhoa, display, valid_from, valid_to, thu_tu}
    Display format: 'K25 Sản (01/00 → ...)' including makhoa_xml for clarity.
    Each row from lookup_khoa is shown individually (no deduplication).
    valid_from / valid_to are raw int (YYYYMMDD) or None.
    """
    full_id = get_full_table_id(LOOKUP_KHOA_TABLE)
    query = (
        f"SELECT makhoa_xml, short_name, valid_from, valid_to, thu_tu "
        f"FROM `{full_id}` ORDER BY short_name, makhoa_xml, valid_from"
    )
    df = run_query(query)
    if df is None or df.empty:
        return []

    options = []
    for _, row in df.iterrows():
        makhoa = row.get("makhoa_xml", "")
        name = row["short_name"]
        vf = row.get("valid_from")
        vt = row.get("valid_to")
        thu_tu = row.get("thu_tu")

        # Raw int values (None if missing)
        vf_raw = int(vf) if pd.notna(vf) and vf else None
        vt_raw = int(vt) if pd.notna(vt) and vt else None
        thu_tu_raw = int(thu_tu) if pd.notna(thu_tu) and thu_tu else None

        # Format valid_from
        if vf_raw:
            vf_str = f"{(vf_raw % 10000) // 100:02d}/{str(vf_raw)[:4][2:]}"
        else:
            vf_str = "?"

        # Format valid_to
        if vt_raw:
            vt_str = f"{(vt_raw % 10000) // 100:02d}/{str(vt_raw)[:4][2:]}"
        else:
            vt_str = "..."

        display = f"{makhoa} {name} ({vf_str} → {vt_str})"
        options.append({
            "short_name": name,
            "makhoa": makhoa,
            "display": display,
            "valid_from": vf_raw,
            "valid_to": vt_raw,
            "thu_tu": thu_tu_raw,
        })
    return options


# ─── Merge Khoa Tab UI ───────────────────────────────────────────────────────

def _render_merge_tab():
    """Render the department merge management tab."""

    # ── Load data ──
    if "merge_groups" not in st.session_state or st.session_state.get("merge_reload"):
        st.session_state["merge_groups"] = _load_merge_groups()
        st.session_state["merge_reload"] = False

    groups = st.session_state["merge_groups"]
    khoa_options = _load_khoa_options()
    all_displays = [o["display"] for o in khoa_options]
    display_to_name = {o["display"]: o["short_name"] for o in khoa_options}
    display_to_option = {o["display"]: o for o in khoa_options}
    # One short_name can have multiple display entries (different makhoa / validity)
    name_to_displays: dict[str, list[str]] = {}
    for o in khoa_options:
        name_to_displays.setdefault(o["short_name"], []).append(o["display"])

    if not khoa_options:
        st.warning("Chưa có dữ liệu bảng Khoa. Vui lòng thêm dữ liệu trong tab Khoa trước.")
        return

    st.markdown(
        f"<div style='font-size:13px;color:#64748b;margin-bottom:8px;'>"
        f"Quản lý nhóm gộp khoa · <b>{len(groups)}</b> nhóm"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Render each merge group as a card ──
    changed = False
    groups_to_delete = []

    for gi, group in enumerate(groups):
        with st.container(border=True):
            col_target, col_del = st.columns([5, 1])

            with col_target:
                # Target khoa dropdown
                # Find first matching display for target short_name
                target_displays = name_to_displays.get(group["target_khoa"], [])
                target_display = target_displays[0] if target_displays else group["target_khoa"]
                target_idx = 0
                if target_display in all_displays:
                    target_idx = all_displays.index(target_display)

                new_target_display = st.selectbox(
                    "Khoa đích",
                    all_displays,
                    index=target_idx,
                    key=f"merge_target_{gi}",
                )
                new_target = display_to_name.get(new_target_display, new_target_display)
                if new_target != group["target_khoa"]:
                    group["target_khoa"] = new_target
                    # Reset selected displays when target changes
                    ss_key_reset = f"merge_srcs_{gi}"
                    if ss_key_reset in st.session_state:
                        del st.session_state[ss_key_reset]
                    changed = True

            with col_del:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Xóa nhóm", key=f"merge_del_{gi}", use_container_width=True):
                    groups_to_delete.append(gi)

            # ── Determine target valid_from for smart source filtering ──
            target_option = display_to_option.get(new_target_display)
            target_valid_from = target_option["valid_from"] if target_option else None

            # Source khoa – dynamic dropdown pattern
            # Exclude target khoa and sources already used in other groups
            other_group_sources = set()
            for ogi, og in enumerate(groups):
                if ogi != gi:
                    other_group_sources.update(og["sources"])

            # Filter: exclude target, exclude sources in other groups,
            # and only show khoa that expired before target started
            # or have no validity dates but have thu_tu
            def _is_eligible_source(o: dict) -> bool:
                if o["short_name"] == new_target:
                    return False
                if o["short_name"] in other_group_sources:
                    return False
                # If target has a valid_from, filter sources by validity
                if target_valid_from:
                    vt = o.get("valid_to")
                    vf = o.get("valid_from")
                    # Case 1: source has valid_to that is before target's valid_from
                    if vt and vt < target_valid_from:
                        return True
                    # Case 2: no validity dates but has thu_tu
                    if not vf and not vt and o.get("thu_tu"):
                        return True
                    return False
                # No target valid_from → show all
                return True

            available_all = [o for o in khoa_options if _is_eligible_source(o)]

            # ── Track selected displays independently in session state ──
            ss_key = f"merge_srcs_{gi}"
            if ss_key not in st.session_state:
                # Init from saved group sources: one display per source
                avail_display_set = {o["display"] for o in available_all}
                init_displays = []
                for s in group["sources"]:
                    for d in name_to_displays.get(s, []):
                        if d in avail_display_set:
                            init_displays.append(d)
                            break  # pick first available display per source
                st.session_state[ss_key] = init_displays

            selected_displays: list[str] = st.session_state[ss_key]

            # ── Render each selected source as a row ──
            st.markdown("**Gộp từ các khoa:**")
            display_to_remove = None
            for si, sel_d in enumerate(selected_displays):
                c_label, c_del = st.columns([5, 1])
                with c_label:
                    st.markdown(
                        f"<div style='background:#e8eaf6;border-radius:6px;"
                        f"padding:6px 12px;margin-bottom:4px;font-size:14px;'>"
                        f"{sel_d}</div>",
                        unsafe_allow_html=True,
                    )
                with c_del:
                    if st.button("✕", key=f"merge_src_del_{gi}_{si}"):
                        display_to_remove = sel_d

            # Handle removal — remove exact display entry only
            if display_to_remove:
                st.session_state[ss_key] = [
                    d for d in selected_displays if d != display_to_remove
                ]
                # Sync short_names back to group
                seen = set()
                group["sources"] = []
                for d in st.session_state[ss_key]:
                    sn = display_to_name.get(d, d)
                    if sn not in seen:
                        seen.add(sn)
                        group["sources"].append(sn)
                st.session_state["merge_groups"] = groups
                st.rerun()

            # ── Empty dropdown to add next source (sorted by makhoa) ──
            already_shown = set(selected_displays)
            remaining = sorted(
                [o["display"] for o in available_all if o["display"] not in already_shown],
                key=lambda d: display_to_option.get(d, {}).get("makhoa", d),
            )

            if remaining:
                placeholder = "-- Chọn khoa để thêm --"
                add_choice = st.selectbox(
                    "Thêm khoa",
                    [placeholder] + remaining,
                    index=0,
                    key=f"merge_src_add_{gi}",
                    label_visibility="collapsed",
                )
                if add_choice != placeholder:
                    selected_displays.append(add_choice)
                    st.session_state[ss_key] = selected_displays
                    # Sync short_names back to group
                    sn = display_to_name.get(add_choice, add_choice)
                    if sn not in group["sources"]:
                        group["sources"].append(sn)
                    st.session_state["merge_groups"] = groups
                    st.rerun()

    # Handle deletions
    if groups_to_delete:
        for gi in sorted(groups_to_delete, reverse=True):
            groups.pop(gi)
        st.session_state["merge_groups"] = groups
        st.rerun()

    # ── Add new group button ──
    if st.button("➕ Thêm nhóm gộp mới", key="merge_add"):
        groups.append({"target_khoa": khoa_options[0]["short_name"], "sources": []})
        st.session_state["merge_groups"] = groups
        st.rerun()

    # ── Save button ──
    st.markdown("---")
    if st.button("💾 Lưu cấu hình gộp khoa", key="merge_save", type="primary"):
        # Validate: no empty sources
        valid = True
        for g in groups:
            if not g["sources"]:
                st.error(f"Nhóm '{g['target_khoa']}' chưa có khoa nguồn nào!")
                valid = False
                break
            # Check no overlap: source can't appear in multiple groups
        all_sources = []
        for g in groups:
            for s in g["sources"]:
                if s in all_sources:
                    st.error(f"Khoa '{s}' xuất hiện trong nhiều nhóm gộp!")
                    valid = False
                    break
                all_sources.append(s)
            if not valid:
                break

        if valid:
            try:
                with st.spinner("⏳ Đang lưu cấu hình gộp khoa..."):
                    _save_merge_groups(groups)
                    st.cache_data.clear()
                st.success(f"✅ Đã lưu {len(groups)} nhóm gộp khoa!")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")


# ─── Main render ──────────────────────────────────────────────────────────────

def render():
    """Render trang Cài đặt."""

    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #059669, #0d9488);">
        <h1>⚙️ Cài đặt bảng mã</h1>
        <p>Quản lý bảng lookup: Loại KCB · Cơ sở KCB · Khoa · Profiles · Gộp khoa</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Tab navigation ──
    tab_names = list(TABLE_CONFIGS.keys()) + ["📊 Profiles", "🔀 Gộp khoa"]
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
                        with st.spinner(f"⏳ Đang lưu `{table_name}`..."):
                            num_rows = _save_table(table_name, edited_df, schema)
                            st.session_state[data_key] = edited_df
                            # Clear cache to reflect changes in overview
                            st.cache_data.clear()
                        st.success(f"✅ Đã lưu {num_rows} dòng vào `{table_name}`!")
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")
            with col2:
                if st.button(f"🔄 Tải lại", key=f"reload_{table_name}"):
                    st.session_state[f"{data_key}_reload"] = True
                    st.rerun()

    # Profiles tab
    with tabs[-2]:
        _render_profiles_tab()

    # Merge Khoa tab
    with tabs[-1]:
        _render_merge_tab()
