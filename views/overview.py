"""
views/overview.py - Trang Quản lý số liệu (Tailwind-in-Streamlit)
===================================================================
3 tab bên trong:
  - Số liệu tổng hợp: Bảng pivot tháng × CSKCB × nội/ngoại trú
  - Quản lý số liệu: Xem thống kê, xóa dữ liệu theo tháng
  - Import: Upload dữ liệu Excel lên BigQuery
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from bq_helper import run_query, get_client, get_full_table_id
from config import (
    PROJECT_ID, DATASET_ID, VIEW_ID, TABLE_ID, FULL_TABLE_ID,
    SHEET_NAME, LOCATION,
    LOOKUP_CSKCB_TABLE, LOOKUP_KHOA_TABLE, LOOKUP_LOAIKCB_TABLE,
)
from tw_components import (
    page_header, section_title, metric_card, metric_row,
    data_table, info_banner, card_list_item, divider,
    paginated_dataframe,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SỐ LIỆU TỔNG HỢP (pivot table - original overview)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_available_years() -> list:
    """Lấy danh sách năm có trong database."""
    query = f"""
        SELECT DISTINCT nam_qt
        FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}`
        ORDER BY nam_qt DESC
    """
    df = run_query(query)
    return df["nam_qt"].tolist()


@st.cache_data(ttl=300)
def _load_overview_data(nam_qt: int) -> pd.DataFrame:
    """Truy vấn dữ liệu tổng hợp theo tháng, ml2, CSKCB."""
    query = f"""
        SELECT
            thang_qt,
            ml2,
            v.ma_cskcb,
            cs.ten_cskcb,
            COUNT(*) AS so_luot,
            SUM(t_tongchi) AS tong_chi
        FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}` v
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.lookup_cskcb` cs
            ON v.ma_cskcb = CAST(cs.ma_cskcb AS STRING)
            AND cs.valid_from <= ({nam_qt} * 10000 + v.thang_qt * 100 + 1)
            AND (cs.valid_to IS NULL OR cs.valid_to >= ({nam_qt} * 10000 + v.thang_qt * 100 + 1))
        WHERE nam_qt = {nam_qt}
        GROUP BY thang_qt, ml2, v.ma_cskcb, cs.ten_cskcb
        ORDER BY thang_qt, ml2, v.ma_cskcb
    """
    return run_query(query)


def _format_number(val, metric: str) -> str:
    """Format số theo metric."""
    if pd.isna(val) or val == 0:
        return ""
    if metric == "tong_chi":
        return f"{val:,.0f}"
    else:
        return f"{int(val):,}"


def _build_pivot_table(data: pd.DataFrame, metric: str) -> tuple:
    """Xây dựng bảng pivot từ dữ liệu tổng hợp. Returns (df, ngoai_cskcb_names, noi_cskcb_names)."""
    if data.empty:
        return pd.DataFrame(), [], []

    # Xác định các CSKCB có dữ liệu theo từng loại
    ngoai_tru = data[data["ml2"] == "Ngoại trú"]
    noi_tru = data[data["ml2"] == "Nội trú"]

    ngoai_cskcb = sorted(ngoai_tru[["ma_cskcb", "ten_cskcb"]].drop_duplicates().values.tolist())
    noi_cskcb = sorted(noi_tru[["ma_cskcb", "ten_cskcb"]].drop_duplicates().values.tolist())

    # Build pivot data
    rows = []
    for thang in range(1, 13):
        row = {"Tháng": f"T{thang:02d}"}

        # Ngoại trú columns
        thang_ngoai = ngoai_tru[ngoai_tru["thang_qt"] == thang]
        tong_ngoai = 0
        for ma, ten in ngoai_cskcb:
            cskcb_data = thang_ngoai[thang_ngoai["ma_cskcb"] == ma]
            val = cskcb_data[metric].sum() if not cskcb_data.empty else 0
            row[f"Ngoại trú|{ten}"] = val
            tong_ngoai += val
        row["Ngoại trú|Tổng"] = tong_ngoai

        # Nội trú columns
        thang_noi = noi_tru[noi_tru["thang_qt"] == thang]
        tong_noi = 0
        for ma, ten in noi_cskcb:
            cskcb_data = thang_noi[thang_noi["ma_cskcb"] == ma]
            val = cskcb_data[metric].sum() if not cskcb_data.empty else 0
            row[f"Nội trú|{ten}"] = val
            tong_noi += val
        row["Nội trú|Tổng"] = tong_noi

        # Tổng cộng
        row["TỔNG CỘNG"] = tong_ngoai + tong_noi
        rows.append(row)

    df = pd.DataFrame(rows)

    # Thêm dòng tổng
    total_row = {"Tháng": "TỔNG NĂM"}
    for col in df.columns:
        if col != "Tháng":
            total_row[col] = df[col].sum()
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

    return df, [ten for _, ten in ngoai_cskcb], [ten for _, ten in noi_cskcb]


def _render_tab_overview():
    """Render tab Số liệu tổng hợp."""

    # ── Filters ──
    years = _get_available_years()
    if not years:
        st.markdown(info_banner("Chưa có dữ liệu trong database.", "warning"), unsafe_allow_html=True)
        return

    metric_options = {"Số lượt KCB": "so_luot", "Tổng chi phí (VNĐ)": "tong_chi"}
    metric_labels = list(metric_options.keys())

    # Restore previous selections from persistent session_state vars
    default_year_idx = 0
    if "_saved_ov_year" in st.session_state:
        saved = st.session_state._saved_ov_year
        if saved in years:
            default_year_idx = years.index(saved)

    default_metric_idx = 0
    if "_saved_ov_metric" in st.session_state:
        saved = st.session_state._saved_ov_metric
        if saved in metric_labels:
            default_metric_idx = metric_labels.index(saved)

    def _on_year_change():
        st.session_state._saved_ov_year = st.session_state._wgt_ov_year

    def _on_metric_change():
        st.session_state._saved_ov_metric = st.session_state._wgt_ov_metric

    col1, col2 = st.columns([1, 1])
    with col1:
        selected_year = st.selectbox(
            "📅 Năm quyết toán", years,
            index=default_year_idx,
            key="_wgt_ov_year",
            on_change=_on_year_change,
        )
        st.session_state._saved_ov_year = selected_year
    with col2:
        metric_label = st.selectbox(
            "📈 Chỉ số hiển thị", metric_labels,
            index=default_metric_idx,
            key="_wgt_ov_metric",
            on_change=_on_metric_change,
        )
        st.session_state._saved_ov_metric = metric_label
        metric = metric_options[metric_label]

    # ── Load data ──
    with st.spinner("⏳ Đang truy vấn dữ liệu..."):
        data = _load_overview_data(selected_year)

    if data.empty:
        st.markdown(info_banner(f"Không có dữ liệu cho năm {selected_year}.", "info"), unsafe_allow_html=True)
        return

    # ── Build & display pivot table ──
    pivot, ngoai_names, noi_names = _build_pivot_table(data, metric)

    if pivot.empty:
        st.markdown(info_banner("Không có dữ liệu để hiển thị.", "info"), unsafe_allow_html=True)
        return

    # Hiển thị summary metrics
    total_row = pivot.iloc[-1]
    unit = " VNĐ" if metric == "tong_chi" else " lượt"

    val_ngoai = total_row.get("Ngoại trú|Tổng", 0)
    val_noi = total_row.get("Nội trú|Tổng", 0)
    val_tong = total_row.get("TỔNG CỘNG", 0)

    cards = metric_row([
        metric_card("Tổng Ngoại trú", f"{val_ngoai:,.0f}{unit}", "🔵", "blue"),
        metric_card("Tổng Nội trú", f"{val_noi:,.0f}{unit}", "🟠", "orange"),
        metric_card("Tổng cộng", f"{val_tong:,.0f}{unit}", "📊", "green"),
    ])
    st.markdown(cards, unsafe_allow_html=True)

    # ── Render pivot table as HTML ──
    _render_html_table(pivot, ngoai_names, noi_names, metric)

    # ── Raw data expander ──
    with st.expander("🔍 Xem dữ liệu chi tiết"):
        st.dataframe(data, use_container_width=True, hide_index=True)


def _render_html_table(pivot: pd.DataFrame, ngoai_names: list, noi_names: list, metric: str):
    """Render bảng pivot dạng HTML với multi-level headers (inline CSS)."""

    fmt = lambda v: f"{v:,.0f}" if pd.notna(v) and v != 0 else ""

    # Build column groups
    ngoai_cols = [f"Ngoại trú|{n}" for n in ngoai_names] + ["Ngoại trú|Tổng"]
    noi_cols = [f"Nội trú|{n}" for n in noi_names] + ["Nội trú|Tổng"]

    ngoai_span = len(ngoai_cols)
    noi_span = len(noi_cols)

    # Common styles
    th_base = "padding:10px 14px;text-align:center;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;font-family:'Inter',sans-serif;"
    td_pad = "padding:8px 14px;"

    # Table wrapper
    html = """
    <div style="border-radius:0.75rem;border:1px solid var(--border);
                overflow:hidden;margin-bottom:1.5rem;
                box-shadow:var(--shadow-table);">
    <table style="width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;">
    <thead>
    <tr>
    """

    # Row 1: group headers
    html += f'<th style="{th_base}color:var(--text-table-header);background:var(--bg-table-header);border-bottom:1px solid var(--border);" rowspan="2">Tháng</th>'
    if ngoai_span > 0:
        html += f'<th style="{th_base}color:white;background:rgba(37,99,235,0.8);border-bottom:1px solid rgba(96,165,250,0.3);" colspan="{ngoai_span}">💵 Ngoại trú</th>'
    if noi_span > 0:
        html += f'<th style="{th_base}color:white;background:rgba(234,88,12,0.8);border-bottom:1px solid rgba(251,146,60,0.3);" colspan="{noi_span}">🏥 Nội trú</th>'
    html += f'<th style="{th_base}color:var(--text-table-header);background:var(--bg-table-header);border-bottom:1px solid var(--border);" rowspan="2">TỔNG CỘNG</th>'
    html += '</tr>'

    # Row 2: sub-column headers
    html += '<tr>'
    for col in ngoai_cols:
        label = col.split("|")[1]
        if label == "Tổng":
            bg = "rgba(30,64,175,0.5)"
            clr = "var(--tbl-subtotal-color)"
            fw = "font-weight:700;"
        else:
            bg = "rgba(30,64,175,0.3)"
            clr = "var(--tbl-subtotal-color)"
            fw = ""
        html += f'<th style="{th_base}color:{clr};background:{bg};border-bottom:1px solid var(--border-muted);{fw}">{label}</th>'
    for col in noi_cols:
        label = col.split("|")[1]
        if label == "Tổng":
            bg = "rgba(154,52,18,0.5)"
            clr = "var(--tbl-subtotal-color)"
            fw = "font-weight:700;"
        else:
            bg = "rgba(154,52,18,0.3)"
            clr = "var(--tbl-subtotal-color)"
            fw = ""
        html += f'<th style="{th_base}color:{clr};background:{bg};border-bottom:1px solid var(--border-muted);{fw}">{label}</th>'
    html += '</tr>'
    html += "</thead>"

    # Table body
    html += "<tbody>"
    for idx, row in pivot.iterrows():
        is_total = row["Tháng"] == "TỔNG NĂM"

        if is_total:
            tr_bg = "var(--bg-table-total)"
            td_color = "var(--text-total)"
            td_fw = "font-weight:700;"
        else:
            tr_bg = "var(--bg-table-row-even)" if idx % 2 == 0 else "var(--bg-table-row-odd)"
            td_color = "var(--text-table)"
            td_fw = ""

        html += f'<tr style="background:{tr_bg};">'

        # Month column
        m_fw = f"font-weight:700;color:var(--text-total);" if is_total else f"font-weight:600;color:var(--text-primary);"
        html += f'<td style="{td_pad}text-align:center;{m_fw}border-right:1px solid var(--border-muted);border-bottom:1px solid var(--border-muted);font-size:0.875rem;">{row["Tháng"]}</td>'

        # Ngoại trú columns
        for col in ngoai_cols:
            is_sub = col.endswith("|Tổng")
            extra = f"font-weight:600;background:rgba(59,130,246,0.05);border-left:1px solid rgba(59,130,246,0.1);" if is_sub and not is_total else ""
            html += f'<td style="{td_pad}text-align:right;color:{td_color};{td_fw}{extra}border-bottom:1px solid var(--border-muted);font-size:0.875rem;">{fmt(row.get(col, 0))}</td>'

        # Nội trú columns
        for col in noi_cols:
            is_sub = col.endswith("|Tổng")
            extra = f"font-weight:600;background:rgba(249,115,22,0.05);border-left:1px solid rgba(249,115,22,0.1);" if is_sub and not is_total else ""
            html += f'<td style="{td_pad}text-align:right;color:{td_color};{td_fw}{extra}border-bottom:1px solid var(--border-muted);font-size:0.875rem;">{fmt(row.get(col, 0))}</td>'

        # Tổng cộng column
        tong_extra = f"font-weight:700;background:rgba(16,185,129,0.05);border-left:1px solid rgba(16,185,129,0.1);" if not is_total else ""
        html += f'<td style="{td_pad}text-align:right;color:{td_color};{td_fw}{tong_extra}border-bottom:1px solid var(--border-muted);font-size:0.875rem;">{fmt(row.get("TỔNG CỘNG", 0))}</td>'
        html += '</tr>'

    html += "</tbody></table></div>"

    st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: QUẢN LÝ SỐ LIỆU
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def _load_data_summary():
    """Load thống kê dữ liệu theo năm/tháng/CSKCB."""
    query = f"""
        SELECT
            nam_qt,
            thang_qt,
            ma_cskcb,
            COUNT(*) AS so_dong,
            SUM(t_tongchi) AS tong_chi,
            MIN(upload_timestamp) AS upload_tu,
            MAX(upload_timestamp) AS upload_den,
            STRING_AGG(DISTINCT source_file, ', ') AS source_files
        FROM `{FULL_TABLE_ID}`
        GROUP BY nam_qt, thang_qt, ma_cskcb
        ORDER BY nam_qt DESC, thang_qt DESC, ma_cskcb
    """
    return run_query(query)


@st.cache_data(ttl=60)
def _load_total_rows():
    """Lấy tổng số dòng trong bảng chính."""
    query = f"SELECT COUNT(*) AS total FROM `{FULL_TABLE_ID}`"
    df = run_query(query)
    return int(df["total"].iloc[0]) if not df.empty else 0


@st.cache_data(ttl=60)
def _load_available_years():
    """Lấy danh sách năm quyết toán có trong bảng."""
    query = f"SELECT DISTINCT nam_qt FROM `{FULL_TABLE_ID}` ORDER BY nam_qt DESC"
    df = run_query(query)
    return df["nam_qt"].astype(int).tolist() if not df.empty else []


_MANAGE_EXCLUDE_COLS = {"upload_timestamp", "source_file"}

# Default columns to search — commonly useful text/code fields
_DEFAULT_SEARCH_COLS = [
    "ho_ten", "ma_bn", "ma_the", "ma_benh", "ma_benhkhac",
    "dia_chi", "khoa", "ten_cskcb", "ma_khoa", "ma_cskcb",
]


@st.cache_data(ttl=300)
def _load_manage_data(nam_qt: int) -> pd.DataFrame:
    """Load toàn bộ dữ liệu từ VIEW enriched theo năm quyết toán."""
    view_full = f"{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}"
    query = f"SELECT * FROM `{view_full}` WHERE nam_qt = {nam_qt}"
    df = run_query(query)
    # Drop upload metadata columns
    drop_cols = [c for c in _MANAGE_EXCLUDE_COLS if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df


@st.cache_data(ttl=300)
def _load_manage_data_range(from_year: int, to_year: int) -> pd.DataFrame:
    """Load toàn bộ dữ liệu từ VIEW enriched theo khoảng năm."""
    view_full = f"{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}"
    query = f"SELECT * FROM `{view_full}` WHERE nam_qt BETWEEN {from_year} AND {to_year} ORDER BY nam_qt DESC, thang_qt DESC, ma_cskcb"
    df = run_query(query)
    drop_cols = [c for c in _MANAGE_EXCLUDE_COLS if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df


def _search_bigquery(conditions: list, from_year: int, to_year: int, limit: int = 10000) -> pd.DataFrame:
    """Search trực tiếp trên BigQuery với các điều kiện multi-condition."""
    view_full = f"{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}"

    # Base WHERE: year range
    where_parts = [f"nam_qt BETWEEN {from_year} AND {to_year}"]

    # Build condition clauses
    active_conds = [c for c in conditions if c.get("keyword", "").strip()]
    cond_clauses = []
    for idx, cond in enumerate(active_conds):
        keyword = cond["keyword"].strip().replace("'", "\\'")
        field = cond["field"]
        clause = f"LOWER(CAST(`{field}` AS STRING)) LIKE '%{keyword.lower()}%'"
        cond_clauses.append({"clause": clause, "operator": cond.get("operator", "AND")})

    if cond_clauses:
        # Build combined condition expression
        expr = cond_clauses[0]["clause"]
        for i in range(1, len(cond_clauses)):
            op = cond_clauses[i]["operator"]
            expr = f"({expr} {op} {cond_clauses[i]['clause']})"
        where_parts.append(f"({expr})")

    where_sql = " AND ".join(where_parts)
    query = f"SELECT * FROM `{view_full}` WHERE {where_sql} LIMIT {limit}"
    df = run_query(query)
    drop_cols = [c for c in _MANAGE_EXCLUDE_COLS if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df


def _count_bigquery(from_year: int, to_year: int) -> int:
    """Đếm nhanh tổng dòng theo khoảng năm (cho metadata)."""
    view_full = f"{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}"
    query = f"SELECT COUNT(*) AS total FROM `{view_full}` WHERE nam_qt BETWEEN {from_year} AND {to_year}"
    df = run_query(query)
    return int(df["total"].iloc[0]) if not df.empty else 0


def _render_tab_manage():
    """Render tab Quản lý số liệu."""

    st.markdown(section_title("Quản lý số liệu", "📋"), unsafe_allow_html=True)

    # Show delete success toast if pending
    _del_msg = st.session_state.pop("_mgmt_delete_success", None)
    if _del_msg:
        st.toast(_del_msg, icon="✅")

    # ── Step 1: Year Range + Method Selector ──
    try:
        years = _load_available_years()
    except Exception as e:
        st.error(f"❌ Lỗi truy vấn BigQuery: {e}")
        return

    if not years:
        st.markdown(info_banner("Chưa có dữ liệu trên BigQuery.", "info"), unsafe_allow_html=True)
        return

    _METHOD_OPTIONS = ["🧠 Tự động", "💾 RAM", "☁️ BigQuery"]
    _AUTO_THRESHOLD = 3  # ≤ 3 years → RAM, > 3 → BigQuery

    col_y1, col_y2, col_method, col_btn = st.columns([1, 1, 1.2, 1])

    with col_y1:
        from_year = st.selectbox(
            "Năm bắt đầu:",
            years,
            key="_mgmt_from_year",
        )

    with col_y2:
        # Only show years >= from_year
        end_years = [y for y in years if y >= from_year]
        # Default to the max year available
        default_end_idx = 0  # First item is max since years is DESC
        to_year = st.selectbox(
            "Năm kết thúc:",
            end_years,
            index=default_end_idx,
            key="_mgmt_to_year",
        )
        # Ensure to_year >= from_year
        if to_year < from_year:
            to_year = from_year

    with col_method:
        selected_method = st.selectbox(
            "Phương pháp:",
            _METHOD_OPTIONS,
            key="_mgmt_method",
        )

    # Determine actual method
    n_years = to_year - from_year + 1
    if selected_method == "🧠 Tự động":
        actual_method = "RAM" if n_years <= _AUTO_THRESHOLD else "BigQuery"
    elif selected_method == "💾 RAM":
        actual_method = "RAM"
    else:
        actual_method = "BigQuery"

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        load_clicked = st.button("📥 Tải dữ liệu", type="primary", key="_mgmt_load_btn")

    # Show loading status for data load
    if load_clicked:
        _load_status = st.status(f"⏳ Đang tải dữ liệu {from_year}–{to_year}...", expanded=True, state="running")

    # Show method hint
    method_icon = "💾" if actual_method == "RAM" else "☁️"
    st.markdown(
        f"<div style='font-size:0.75rem;color:var(--text-muted);margin-top:-0.5rem;'>"
        f"{method_icon} Phương pháp: <strong>{actual_method}</strong> ({n_years} năm, "
        f"từ {from_year} đến {to_year})</div>",
        unsafe_allow_html=True,
    )

    # ── Load data ──
    _loaded_key = "_mgmt_loaded_data"
    _loaded_range_key = "_mgmt_loaded_range"
    _loaded_method_key = "_mgmt_loaded_method"

    if load_clicked:
        current_range = (from_year, to_year)
        if actual_method == "RAM":
            _load_status.write(f"💾 Nạp dữ liệu {from_year}–{to_year} vào RAM...")
            data = _load_manage_data_range(from_year, to_year)
            st.session_state[_loaded_key] = data
            _load_status.update(label=f"✅ Đã tải {len(data):,} dòng ({from_year}–{to_year})", state="complete", expanded=False)
        else:
            _load_status.write(f"☁️ Đếm dữ liệu {from_year}–{to_year} trên BigQuery...")
            total_count = _count_bigquery(from_year, to_year)
            st.session_state[_loaded_key] = None
            st.session_state["_mgmt_bq_total"] = total_count
            _load_status.update(label=f"✅ Sẵn sàng ({total_count:,} dòng, BigQuery)", state="complete", expanded=False)

        st.session_state[_loaded_range_key] = current_range
        st.session_state[_loaded_method_key] = actual_method

        # Reset search conditions to single empty condition
        st.session_state["_mgmt_search_conditions"] = [{"field": "", "keyword": ""}]
        # Reset pagination
        st.session_state["_mgmt_page"] = 0
        # Clear any pending search action
        if "_mgmt_action_search" in st.session_state:
            del st.session_state["_mgmt_action_search"]

    # Retrieve from session_state
    loaded_range = st.session_state.get(_loaded_range_key)
    loaded_method = st.session_state.get(_loaded_method_key, "RAM")

    if loaded_range != (from_year, to_year):
        st.markdown(info_banner(
            f"Chọn khoảng năm và bấm <strong>Tải dữ liệu</strong> để hiển thị.",
            "info"
        ), unsafe_allow_html=True)
        return

    data = st.session_state.get(_loaded_key)

    if loaded_method == "RAM":
        if data is None or data.empty:
            st.markdown(info_banner(
                f"Năm {from_year}–{to_year}: không có dữ liệu.", "info"
            ), unsafe_allow_html=True)
            return

    # ── Metrics ──
    if loaded_method == "RAM":
        total = len(data)
        n_months = data[["nam_qt", "thang_qt"]].drop_duplicates().shape[0]
        n_cskcb = data["ma_cskcb"].nunique()
    else:
        total = st.session_state.get("_mgmt_bq_total", 0)
        n_months = to_year - from_year + 1
        n_cskcb = "–"

    cards = metric_row([
        metric_card("Số dòng", f"{total:,}", "📊", "blue"),
        metric_card("Số tháng" if loaded_method == "RAM" else "Số năm", f"{n_months}", "📅", "cyan"),
        metric_card("Số CSKCB", f"{n_cskcb}", "🏥", "purple"),
    ])
    st.markdown(cards, unsafe_allow_html=True)

    st.markdown(divider(), unsafe_allow_html=True)

    # ── Step 2: Multi-condition Search Builder ──
    st.markdown(section_title("Dữ liệu chi tiết", "🔍"), unsafe_allow_html=True)

    # ── CSS/JS: inline clear X inside search inputs ──
    # Inject CSS into parent document and JS to convert inputs to type="search"
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        const doc = window.parent.document;

        // Inject CSS for styled search cancel button
        if (!doc.getElementById('_mgmt_search_css')) {
            const style = doc.createElement('style');
            style.id = '_mgmt_search_css';
            style.textContent = `
                div[data-testid="stTextInput"] input[type="search"] {
                    -webkit-appearance: searchfield !important;
                }
                div[data-testid="stTextInput"] input[type="search"]::-webkit-search-cancel-button {
                    -webkit-appearance: none;
                    display: inline-block;
                    height: 16px;
                    width: 16px;
                    cursor: pointer;
                    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='18' y1='6' x2='6' y2='18'/%3E%3Cline x1='6' y1='6' x2='18' y2='18'/%3E%3C/svg%3E") center/contain no-repeat;
                    opacity: 0.4;
                    transition: opacity 0.2s;
                }
                div[data-testid="stTextInput"] input[type="search"]::-webkit-search-cancel-button:hover {
                    opacity: 0.9;
                }
            `;
            doc.head.appendChild(style);
        }

        // Convert keyword inputs to type="search" and add clear event handler
        function convertInputs() {
            doc.querySelectorAll('input[aria-label^="Từ khóa"]').forEach(input => {
                if (input.type !== 'search') {
                    input.type = 'search';
                    // When native X is clicked, trigger React's change detection
                    input.addEventListener('search', function() {
                        if (this.value === '') {
                            // Dispatch input event so Streamlit/React picks up the change
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                                window.parent.HTMLInputElement.prototype, 'value'
                            ).set;
                            nativeInputValueSetter.call(this, '');
                            this.dispatchEvent(new Event('input', { bubbles: true }));
                            this.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    });
                }
            });
        }

        convertInputs();
        const obs = new MutationObserver(convertInputs);
        obs.observe(doc.body, { childList: true, subtree: true });
    })();
    </script>
    """, height=0)

    # Get column list (from data if RAM, or from a quick schema query if BQ)
    if loaded_method == "RAM" and data is not None:
        all_columns = list(data.columns)
    else:
        # Fetch column names from BigQuery schema
        _cols_cache_key = "_mgmt_bq_columns"
        if _cols_cache_key not in st.session_state:
            view_full = f"{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}"
            schema_df = run_query(f"SELECT * FROM `{view_full}` LIMIT 0")
            st.session_state[_cols_cache_key] = [c for c in schema_df.columns if c not in _MANAGE_EXCLUDE_COLS]
        all_columns = st.session_state[_cols_cache_key]

    # ── Session state for conditions ──
    _cond_key = "_mgmt_search_conditions"
    _default_field = all_columns[0] if all_columns else ""

    if _cond_key not in st.session_state:
        # Each condition: {"field": str, "keyword": str, "operator": "AND"/"OR"}
        # operator is the combinator with the PREVIOUS condition (ignored for first)
        st.session_state[_cond_key] = [{"field": _default_field, "keyword": ""}]

    conditions = st.session_state[_cond_key]

    # ── Handle add / delete actions (process before rendering) ──
    _action_add_key = "_mgmt_action_add"
    _action_del_key = "_mgmt_action_del"

    if st.session_state.get(_action_add_key, False):
        conditions.append({"field": _default_field, "keyword": "", "operator": "AND"})
        st.session_state[_cond_key] = conditions
        del st.session_state[_action_add_key]
        st.rerun()

    # Check for delete action
    _del_idx = st.session_state.get(_action_del_key, None)
    if _del_idx is not None and 1 <= _del_idx < len(conditions):
        conditions.pop(_del_idx)
        st.session_state[_cond_key] = conditions
        del st.session_state[_action_del_key]
        st.rerun()

    # ── Render condition rows ──
    n_conds = len(conditions)

    for i, cond in enumerate(conditions):
        # ── AND/OR radio (between conditions, shown for i >= 1) ──
        if i >= 1:
            op_val = st.radio(
                f"Điều kiện {i + 1}",
                ["AND", "OR"],
                index=0 if cond.get("operator", "AND") == "AND" else 1,
                horizontal=True,
                key=f"_mgmt_cond_op_{i}",
                label_visibility="collapsed",
            )
            conditions[i]["operator"] = op_val

        # ── Condition row: [field dropdown] [search box] [➕] [🗑️] ──
        is_last = i == n_conds - 1

        if i == 0:
            # First condition: [field] [search] [➕ add]
            c_field, c_search, c_add = st.columns([1.5, 4, 0.4])
        elif is_last:
            # Last condition (not first): [field] [search] [➕ add] [🗑️ delete]
            c_field, c_search, c_add, c_del = st.columns([1.5, 4, 0.4, 0.4])
        else:
            # Middle condition: [field] [search] [🗑️ delete]
            c_field, c_search, c_del = st.columns([1.5, 4, 0.4])

        with c_field:
            field_idx = all_columns.index(cond["field"]) if cond["field"] in all_columns else 0
            sel_field = st.selectbox(
                f"Trường {i + 1}",
                all_columns,
                index=field_idx,
                key=f"_mgmt_cond_field_{i}",
                label_visibility="collapsed",
            )
            conditions[i]["field"] = sel_field

        with c_search:
            kw = st.text_input(
                f"Từ khóa {i + 1}",
                value=cond.get("keyword", ""),
                placeholder=f"Tìm trong \"{sel_field}\"...",
                key=f"_mgmt_cond_kw_{i}",
                label_visibility="collapsed",
            )
            conditions[i]["keyword"] = kw

        # ➕ add button (only on last condition)
        if is_last:
            with c_add:
                if st.button("➕", key=f"_mgmt_btn_add_{i}", use_container_width=True):
                    st.session_state[_action_add_key] = True
                    st.rerun()

        # 🗑️ delete button (on conditions >= 1)
        if i >= 1:
            with c_del:
                if st.button("🗑️", key=f"_mgmt_btn_del_{i}", use_container_width=True):
                    st.session_state[_action_del_key] = i
                    st.rerun()

    st.session_state[_cond_key] = conditions

    # ── Search button ──
    _action_search_key = "_mgmt_action_search"
    if st.button("🔍 Tìm kiếm", key="_mgmt_search_go_btn", type="primary"):
        st.session_state[_action_search_key] = True

    # ── Apply search filter ──
    display_df = data if data is not None else pd.DataFrame()
    _is_searching = False

    if st.session_state.get(_action_search_key, False):
        active_conds = [c for c in conditions if c.get("keyword", "").strip()]

        if active_conds:
            _is_searching = True

            if loaded_method == "RAM" and data is not None:
                # ── RAM mode: pandas filter ──
                final_mask = None
                for idx, cond in enumerate(active_conds):
                    keyword = cond["keyword"].lower().strip()
                    field = cond["field"]
                    if field not in data.columns:
                        continue
                    col_values = data[field].fillna("").astype(str).str.lower()
                    cond_mask = col_values.str.contains(keyword, na=False)
                    if final_mask is None:
                        final_mask = cond_mask
                    else:
                        op = cond.get("operator", "AND")
                        if op == "AND":
                            final_mask = final_mask & cond_mask
                        else:
                            final_mask = final_mask | cond_mask
                if final_mask is not None:
                    display_df = data[final_mask]
            else:
                # ── BigQuery mode: server-side search ──
                _search_status = st.status("⏳ Đang tìm kiếm trên BigQuery...", expanded=True, state="running")
                _search_status.write("☁️ Gửi truy vấn đến BigQuery...")
                display_df = _search_bigquery(conditions, from_year, to_year)
                _search_status.update(label=f"✅ Tìm thấy {len(display_df):,} kết quả", state="complete", expanded=False)
                st.session_state["_mgmt_bq_search_result"] = display_df

            # Build summary text
            summary_ops = []
            for j, c in enumerate(active_conds):
                if j > 0:
                    summary_ops.append(f" <strong>{c.get('operator', 'AND')}</strong> ")
                summary_ops.append(f"\"{c['keyword']}\" trong <em>{c['field']}</em>")
            summary_text = "".join(summary_ops)

            st.markdown(info_banner(
                f"Tìm thấy <strong>{len(display_df):,}</strong> / {total:,} dòng "
                f"khớp: {summary_text}"
                + (" (giới hạn 10,000 dòng)" if loaded_method == "BigQuery" and len(display_df) >= 10000 else ""),
                "success" if len(display_df) > 0 else "warning"
            ), unsafe_allow_html=True)

        # Reset search trigger
        del st.session_state[_action_search_key]
    elif loaded_method == "BigQuery":
        # Check if there's a cached BQ search result
        cached_bq = st.session_state.get("_mgmt_bq_search_result")
        if cached_bq is not None:
            display_df = cached_bq
            _is_searching = True

    # In BigQuery mode, if no search has been performed, show instruction
    if loaded_method == "BigQuery" and not _is_searching:
        st.markdown(info_banner(
            "Chế độ <strong>BigQuery</strong>: nhập điều kiện tìm kiếm và bấm "
            "<strong>🔍 Tìm kiếm</strong> để truy vấn dữ liệu.",
            "info"
        ), unsafe_allow_html=True)
        return

    # ── Paginated data table ──
    import math

    _ps_key = "_mgmt_page_size"
    _pg_key = "_mgmt_page"
    _page_sizes = [10, 20, 30, 40, 50, 100]

    if _ps_key not in st.session_state:
        st.session_state[_ps_key] = 20
    if _pg_key not in st.session_state:
        st.session_state[_pg_key] = 0

    page_size = st.session_state[_ps_key]
    total_display = len(display_df)
    total_pages = max(1, math.ceil(total_display / page_size))

    if st.session_state[_pg_key] >= total_pages:
        st.session_state[_pg_key] = total_pages - 1
    if st.session_state[_pg_key] < 0:
        st.session_state[_pg_key] = 0

    current_page = st.session_state[_pg_key]
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_display)
    page_df = display_df.iloc[start_idx:end_idx].copy()

    # ── Data table with native row selection ──
    view_df = page_df.reset_index(drop=True)

    selection = st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="multi-row",
        on_select="rerun",
        key=f"_mgmt_editor_p{current_page}",
    )

    # ── Compact paging bar (below table) ──
    pg_cols1, pg_cols2, pg_cols3, pg_cols4, pg_cols5 = st.columns(
        [1, 0.5, 0.8, 0.5, 2]
    )

    with pg_cols1:
        new_size = st.selectbox(
            "Số dòng/trang",
            _page_sizes,
            index=_page_sizes.index(page_size) if page_size in _page_sizes else 0,
            key="_mgmt_ps_select",
            label_visibility="collapsed",
        )
        if new_size != page_size:
            st.session_state[_ps_key] = new_size
            st.session_state[_pg_key] = 0
            st.rerun()

    with pg_cols2:
        if st.button("◀", key="_mgmt_prev", disabled=(current_page == 0)):
            st.session_state[_pg_key] = current_page - 1
            st.rerun()

    with pg_cols3:
        st.markdown(
            f"<div style='text-align:center;padding:0.3rem 0;color:var(--text-secondary);font-size:0.75rem;'>"
            f"Trang <strong style='color:var(--text-primary);'>{current_page + 1}</strong> / {total_pages}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with pg_cols4:
        if st.button("▶", key="_mgmt_next", disabled=(current_page >= total_pages - 1)):
            st.session_state[_pg_key] = current_page + 1
            st.rerun()

    with pg_cols5:
        st.markdown(
            f"<div style='text-align:right;padding:0.3rem 0;color:var(--text-muted);font-size:0.7rem;'>"
            f"Hiển thị {start_idx + 1:,}–{end_idx:,} / {total_display:,} dòng"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Count selected rows ──
    selected_indices = selection.selection.rows if selection.selection else []
    n_selected = len(selected_indices)

    # ── Delete button with confirmation ──
    if n_selected > 0:
        st.markdown(divider(), unsafe_allow_html=True)

        st.markdown(info_banner(
            f"Đã chọn <strong>{n_selected:,}</strong> dòng. "
            f"Bấm nút bên dưới để xóa các dòng đã chọn khỏi BigQuery.",
            "warning"
        ), unsafe_allow_html=True)

        col_del_btn, col_del_confirm, _ = st.columns([1, 1, 3])
        with col_del_confirm:
            confirm_text = st.text_input(
                "Nhập `XÓA` để xác nhận:",
                key="_mgmt_del_row_confirm",
            )
        with col_del_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(
                f"🗑️ Xóa {n_selected} dòng đã chọn",
                type="primary",
                key="_mgmt_del_row_btn",
            ):
                if confirm_text != "XÓA":
                    st.error("❌ Nhập đúng `XÓA` để xác nhận xóa.")
                else:
                    # Map selected view_df indices back to display_df positions
                    orig_indices = [start_idx + i for i in selected_indices]
                    rows_to_delete = display_df.iloc[orig_indices]

                    client = get_client()
                    progress = st.progress(0)
                    deleted_count = 0

                    for idx, (_, row) in enumerate(rows_to_delete.iterrows()):
                        # Build WHERE clause from composite key
                        conditions = []
                        for col in _ROW_KEY_COLS:
                            val = row.get(col)
                            if pd.isna(val):
                                conditions.append(f"{col} IS NULL")
                            elif isinstance(val, (int, float)):
                                conditions.append(f"{col} = {val}")
                            else:
                                safe_val = str(val).replace("'", "\\'")
                                conditions.append(f"{col} = '{safe_val}'")

                        where_clause = " AND ".join(conditions)
                        delete_q = f"DELETE FROM `{FULL_TABLE_ID}` WHERE {where_clause}"
                        try:
                            client.query(delete_q).result()
                            deleted_count += 1
                        except Exception as e:
                            st.warning(f"⚠️ Lỗi xóa dòng {idx + 1}: {e}")

                        progress.progress((idx + 1) / len(rows_to_delete))

                    # Store success message, clear caches, reload fresh data, then rerun
                    st.session_state["_mgmt_delete_success"] = (
                        f"✅ Đã xóa {deleted_count:,} / {n_selected:,} dòng!"
                    )
                    _clear_all_caches()
                    _load_available_years.clear()
                    _load_manage_data.clear()
                    # Reload fresh data before rerun
                    fresh = _load_manage_data(st.session_state.get("_mgmt_loaded_year", selected_year))
                    st.session_state["_mgmt_loaded_data"] = fresh
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

_ROW_KEY_COLS = ["ma_cskcb", "ma_bn", "ma_loaikcb", "ngay_vao", "ngay_ra"]

# 14 required columns that must be non-empty for a valid row
_REQUIRED_COLS = [
    "ma_bn", "ho_ten", "ngay_sinh", "gioi_tinh", "ma_dkbd", "ma_benh",
    "ngay_vao", "ngay_ra", "t_tongchi", "t_bhtt", "ma_khoa",
    "nam_qt", "thang_qt", "ma_cskcb",
]

# All expected schema columns (excluding metadata)
_SCHEMA_COLS = [
    "stt", "ma_bn", "ho_ten", "ngay_sinh", "gioi_tinh", "dia_chi",
    "ma_the", "ma_dkbd", "gt_the_tu", "gt_the_den", "ma_benh", "ma_benhkhac",
    "ma_lydo_vvien", "ma_noi_chuyen", "ngay_vao", "ngay_ra", "so_ngay_dtri",
    "ket_qua_dtri", "tinh_trang_rv", "t_tongchi", "t_xn", "t_cdha", "t_thuoc",
    "t_mau", "t_pttt", "t_vtyt", "t_dvkt_tyle", "t_thuoc_tyle", "t_vtyt_tyle",
    "t_kham", "t_giuong", "t_vchuyen", "t_bntt", "t_bhtt", "t_ngoaids",
    "ma_khoa", "nam_qt", "thang_qt", "ma_khuvuc", "ma_loaikcb", "ma_cskcb",
    "noi_ttoan", "giam_dinh", "t_xuattoan", "t_nguonkhac", "t_datuyen", "t_vuottran",
]


# ─── Parsing helpers ──────────────────────────────────────────────────────────

def _parse_date_int(val):
    """Chuyển int YYYYMMDD → datetime.date, trả None nếu lỗi."""
    if pd.isna(val):
        return None
    try:
        s = str(int(val))
        return datetime.strptime(s, "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


def _parse_datetime_str(val):
    """Chuyển string '202601020735' → datetime, trả None nếu lỗi."""
    if pd.isna(val):
        return None
    try:
        s = str(val).strip().lstrip("'")
        if len(s) == 12:
            return datetime.strptime(s, "%Y%m%d%H%M")
        elif len(s) == 14:
            return datetime.strptime(s, "%Y%m%d%H%M%S")
        elif len(s) == 8:
            return datetime.strptime(s, "%Y%m%d")
        return None
    except (ValueError, TypeError):
        return None


def _transform_dataframe(df: pd.DataFrame, source_filename: str) -> pd.DataFrame:
    """Chuẩn hóa kiểu dữ liệu cho tất cả các cột."""
    df.columns = [c.lower().strip() for c in df.columns]

    for col in ["ngay_sinh", "gt_the_tu", "gt_the_den"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_date_int)

    for col in ["ngay_vao", "ngay_ra"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_datetime_str)

    str_cols = ["ma_bn", "ma_the", "ma_dkbd", "ma_benh", "ma_benhkhac",
                "ma_noi_chuyen", "ma_khoa", "ma_khuvuc", "ma_cskcb",
                "giam_dinh", "ho_ten", "dia_chi"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) and x != "" else None)
            df[col] = df[col].replace("nan", None)

    float_cols = ["t_tongchi", "t_xn", "t_cdha", "t_thuoc", "t_mau",
                  "t_pttt", "t_vtyt", "t_dvkt_tyle", "t_thuoc_tyle",
                  "t_vtyt_tyle", "t_kham", "t_giuong", "t_vchuyen",
                  "t_bntt", "t_bhtt", "t_ngoaids", "t_xuattoan",
                  "t_nguonkhac", "t_datuyen", "t_vuottran"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    int_cols = ["stt", "gioi_tinh", "ma_lydo_vvien", "so_ngay_dtri",
                "ket_qua_dtri", "tinh_trang_rv", "nam_qt", "thang_qt",
                "ma_loaikcb", "noi_ttoan"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["upload_timestamp"] = datetime.utcnow()
    df["source_file"] = source_filename

    return df


# ─── Sheet auto-detection ─────────────────────────────────────────────────────

def _detect_compatible_sheets(xls) -> list:
    """
    Scan all sheets in the Excel file, return list of compatible sheets.
    A sheet is compatible if its header row contains ALL 14 required columns.
    Returns: [{sheet_name, matched_cols, extra_cols, missing_required}]
    """
    compatible = []
    for sheet_name in xls.sheet_names:
        try:
            header_df = pd.read_excel(xls, sheet_name=sheet_name, nrows=0, engine="openpyxl")
            cols_lower = [c.lower().strip() for c in header_df.columns]

            matched = [c for c in _SCHEMA_COLS if c in cols_lower]
            extra = [c for c in cols_lower if c not in _SCHEMA_COLS]
            missing_required = [c for c in _REQUIRED_COLS if c not in cols_lower]

            if not missing_required:  # All 14 required columns present
                compatible.append({
                    "sheet_name": sheet_name,
                    "matched_cols": matched,
                    "extra_cols": extra,
                    "missing_required": missing_required,
                    "total_cols": len(cols_lower),
                })
        except Exception:
            continue
    return compatible


# ─── Row-level validation ─────────────────────────────────────────────────────

def _validate_rows(df: pd.DataFrame):
    """
    Validate each row: required columns must be non-null and in correct format.
    Returns: (valid_df, invalid_df, issues_report)
    """
    issues = []  # list of (row_idx, column, reason)
    invalid_mask = pd.Series(False, index=df.index)

    for col in _REQUIRED_COLS:
        if col not in df.columns:
            continue

        # Check null / empty
        null_mask = df[col].isna()
        if col in ["ma_bn", "ho_ten", "ma_dkbd", "ma_benh", "ma_khoa", "ma_cskcb"]:
            null_mask = null_mask | (df[col].astype(str).str.strip() == "")

        # Format-specific checks
        if col == "ngay_sinh":
            # After transform, should be a date object or None
            fmt_bad = df[col].apply(lambda x: x is not None and not hasattr(x, 'year'))
            null_mask = null_mask | fmt_bad
        elif col in ["ngay_vao", "ngay_ra"]:
            fmt_bad = df[col].apply(lambda x: x is not None and not hasattr(x, 'hour'))
            null_mask = null_mask | fmt_bad
        elif col == "gioi_tinh":
            fmt_bad = ~df[col].isin([1, 2, 1.0, 2.0]) & ~df[col].isna()
            null_mask = null_mask | fmt_bad
        elif col in ["t_tongchi", "t_bhtt"]:
            fmt_bad = pd.to_numeric(df[col], errors="coerce").isna() & ~df[col].isna()
            null_mask = null_mask | fmt_bad
        elif col == "thang_qt":
            numeric_val = pd.to_numeric(df[col], errors="coerce")
            fmt_bad = (~numeric_val.between(1, 12)) & ~df[col].isna()
            null_mask = null_mask | fmt_bad
        elif col in ["nam_qt"]:
            numeric_val = pd.to_numeric(df[col], errors="coerce")
            fmt_bad = numeric_val.isna() & ~df[col].isna()
            null_mask = null_mask | fmt_bad

        n_bad = null_mask.sum()
        if n_bad > 0:
            issues.append((col, int(n_bad)))
        invalid_mask = invalid_mask | null_mask

    valid_df = df[~invalid_mask].copy()
    invalid_df = df[invalid_mask].copy()

    return valid_df, invalid_df, issues


# ─── Duplicate detection ─────────────────────────────────────────────────────

def _check_duplicates(client, df: pd.DataFrame) -> pd.DataFrame:
    """Kiểm tra trùng lặp row-level. Returns DataFrame với các dòng trùng."""
    try:
        client.get_table(FULL_TABLE_ID)
    except NotFound:
        return pd.DataFrame()

    ma_bn_list = df["ma_bn"].dropna().unique().tolist()
    if not ma_bn_list:
        return pd.DataFrame()

    BATCH_SIZE = 5000
    key_cols_sql = ", ".join(_ROW_KEY_COLS)
    all_bq_rows = []

    for i in range(0, len(ma_bn_list), BATCH_SIZE):
        batch = ma_bn_list[i:i + BATCH_SIZE]
        ma_bn_in = ", ".join([f"'{str(m)}'" for m in batch])
        query = f"""
            SELECT {key_cols_sql}
            FROM `{FULL_TABLE_ID}`
            WHERE ma_bn IN ({ma_bn_in})
        """
        result = client.query(query).to_dataframe()
        if not result.empty:
            all_bq_rows.append(result)

    if not all_bq_rows:
        return pd.DataFrame()

    bq_rows = pd.concat(all_bq_rows, ignore_index=True)
    if bq_rows.empty:
        return pd.DataFrame()

    merge_df = df[_ROW_KEY_COLS].copy()
    for col in ["ma_cskcb", "ma_bn"]:
        merge_df[col] = merge_df[col].astype(str)
        bq_rows[col] = bq_rows[col].astype(str)
    for col in ["ma_loaikcb"]:
        merge_df[col] = pd.to_numeric(merge_df[col], errors="coerce")
        bq_rows[col] = pd.to_numeric(bq_rows[col], errors="coerce")
    for col in ["ngay_vao", "ngay_ra"]:
        merge_df[col] = pd.to_datetime(merge_df[col], errors="coerce")
        bq_rows[col] = pd.to_datetime(bq_rows[col], errors="coerce")

    merged = merge_df.merge(bq_rows, on=_ROW_KEY_COLS, how="inner")
    if merged.empty:
        return pd.DataFrame()

    dup_mask = df[_ROW_KEY_COLS].apply(tuple, axis=1).isin(
        merged[_ROW_KEY_COLS].apply(tuple, axis=1)
    )
    return df[dup_mask]


# ─── Lookup code validation ──────────────────────────────────────────────────

def _check_lookup_codes(client, df: pd.DataFrame) -> list:
    """
    Check ma_cskcb, (ma_cskcb, ma_khoa), and ma_loaikcb against lookup tables.
    Returns list of warning strings.
    """
    warnings = []

    # ── Check ma_cskcb ──
    try:
        cskcb_full_id = get_full_table_id(LOOKUP_CSKCB_TABLE)
        cskcb_df = client.query(f"SELECT DISTINCT ma_cskcb FROM `{cskcb_full_id}`").to_dataframe()
        known_cskcb = set(cskcb_df["ma_cskcb"].dropna().astype(str))
    except Exception:
        known_cskcb = set()

    if known_cskcb:
        upload_cskcb = set(df["ma_cskcb"].dropna().astype(str).unique())
        missing_cskcb = upload_cskcb - known_cskcb
        if missing_cskcb:
            codes = ", ".join(sorted(missing_cskcb))
            warnings.append(f"Mã cơ sở KCB chưa có trong danh mục: <strong>{codes}</strong>")

    # ── Check (ma_cskcb, ma_khoa) pairs ──
    try:
        khoa_full_id = get_full_table_id(LOOKUP_KHOA_TABLE)
        khoa_df = client.query(
            f"SELECT DISTINCT ma_cskcb, makhoa_xml FROM `{khoa_full_id}`"
        ).to_dataframe()
        known_pairs = set(
            zip(khoa_df["ma_cskcb"].astype(str), khoa_df["makhoa_xml"].astype(str))
        )
    except Exception:
        known_pairs = set()

    if known_pairs and "ma_khoa" in df.columns:
        upload_pairs = set(
            zip(
                df["ma_cskcb"].dropna().astype(str),
                df["ma_khoa"].dropna().astype(str),
            )
        )
        missing_pairs = upload_pairs - known_pairs
        if missing_pairs:
            details = ", ".join(
                [f"{khoa} (CSKCB: {cskcb})" for cskcb, khoa in sorted(missing_pairs)]
            )
            warnings.append(f"Mã khoa chưa có trong danh mục: <strong>{details}</strong>")

    # ── Check ma_loaikcb ──
    try:
        loaikcb_full_id = get_full_table_id(LOOKUP_LOAIKCB_TABLE)
        loaikcb_df = client.query(f"SELECT DISTINCT ma_loaikcb FROM `{loaikcb_full_id}`").to_dataframe()
        known_loaikcb = set(loaikcb_df["ma_loaikcb"].dropna().astype(int))
    except Exception:
        known_loaikcb = set()

    if known_loaikcb and "ma_loaikcb" in df.columns:
        upload_loaikcb = set(df["ma_loaikcb"].dropna().astype(int).unique())
        missing_loaikcb = upload_loaikcb - known_loaikcb
        if missing_loaikcb:
            codes = ", ".join([str(c) for c in sorted(missing_loaikcb)])
            warnings.append(f"Mã loại KCB chưa có trong danh mục: <strong>{codes}</strong>")

    return warnings


# ─── Delete duplicates from BigQuery ──────────────────────────────────────────

def _delete_duplicates_from_bq(client, dup_df: pd.DataFrame):
    """Delete exact duplicate rows from BigQuery based on composite key."""
    dup_groups = dup_df.groupby(["nam_qt", "thang_qt", "ma_cskcb"])
    total_deleted = 0
    for (nam, thang, cskcb), group in dup_groups:
        row_conditions = []
        for _, r in group.iterrows():
            ngay_vao_str = r["ngay_vao"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(r["ngay_vao"]) else None
            ngay_ra_str = r["ngay_ra"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(r["ngay_ra"]) else None
            parts = [f"ma_cskcb = '{r['ma_cskcb']}'",
                     f"ma_bn = '{r['ma_bn']}'"]
            parts.append(f"ma_loaikcb = {int(r['ma_loaikcb'])}" if pd.notna(r["ma_loaikcb"]) else "ma_loaikcb IS NULL")
            parts.append(f"ngay_vao = '{ngay_vao_str}'" if ngay_vao_str else "ngay_vao IS NULL")
            parts.append(f"ngay_ra = '{ngay_ra_str}'" if ngay_ra_str else "ngay_ra IS NULL")
            row_conditions.append(f"({' AND '.join(parts)})")

        delete_query = f"""
            DELETE FROM `{FULL_TABLE_ID}`
            WHERE nam_qt = {int(nam)} AND thang_qt = {int(thang)}
              AND ({' OR '.join(row_conditions)})
        """
        client.query(delete_query).result()
        total_deleted += len(group)
    return total_deleted


# ─── Upload helper ────────────────────────────────────────────────────────────

def _clear_all_caches():
    """Clear all @st.cache_data caches across all pages."""
    # -- overview.py caches --
    _load_data_summary.clear()
    _load_total_rows.clear()
    _load_overview_data.clear()

    # -- other pages: clear globally --
    try:
        from views.hospital_stats import _load_hospital_data, _load_cost_periods
        _load_hospital_data.clear()
        _load_cost_periods.clear()
    except Exception:
        pass
    try:
        from views.cost_by_dept import (
            _load_dept_data, _load_dept_summary,
            _load_dept_cost_periods, _load_dept_periods,
            _load_comparison_data, _load_comparison_periods,
        )
        for fn in [_load_dept_data, _load_dept_summary,
                   _load_dept_cost_periods, _load_dept_periods,
                   _load_comparison_data, _load_comparison_periods]:
            fn.clear()
    except Exception:
        pass
    try:
        from views.icd_analysis import (
            _load_icd_data, _load_icd_detail, _load_icd_periods,
        )
        for fn in [_load_icd_data, _load_icd_detail, _load_icd_periods]:
            fn.clear()
    except Exception:
        pass


def _do_upload(client, df: pd.DataFrame, upload_type: str = "new"):
    """Thực hiện upload DataFrame lên BigQuery."""
    from upload_to_bigquery import SCHEMA

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    with st.spinner(f"⏳ Đang upload {len(df):,} dòng lên BigQuery..."):
        job = client.load_table_from_dataframe(df, FULL_TABLE_ID, job_config=job_config)
        job.result()

    table = client.get_table(FULL_TABLE_ID)
    st.toast(f"🎉 Upload thành công! {len(df):,} dòng. Tổng: {table.num_rows:,}", icon="✅")

    # Set flag to prevent double upload & clear all caches
    st.session_state[f"_import_done_{upload_type}"] = True
    _clear_all_caches()
    st.rerun()


# ─── Main import tab render ───────────────────────────────────────────────────

def _render_tab_import():
    """Render tab Import dữ liệu — full validation flow."""

    st.markdown(section_title("Import dữ liệu Excel lên BigQuery", "📥"), unsafe_allow_html=True)
    st.markdown(info_banner(
        f"Upload file Excel chứa dữ liệu thanh toán BHYT. "
        f"Target: <code style='color:var(--accent-light);background:var(--bg-code);padding:0.15rem 0.4rem;"
        f"border-radius:0.25rem;font-size:0.85em;'>{FULL_TABLE_ID}</code>",
        "info"
    ), unsafe_allow_html=True)

    # ── Step 1: File uploader ──
    uploaded_file = st.file_uploader(
        "Chọn file Excel (.xlsx, .xls)",
        type=["xlsx", "xls"],
        key="_import_file_uploader",
    )

    if uploaded_file is None:
        st.markdown(info_banner("Chọn file Excel để bắt đầu.", "info"), unsafe_allow_html=True)
        return

    filename = uploaded_file.name

    # Reset upload flags when a new file is uploaded
    if st.session_state.get("_import_last_file") != filename:
        st.session_state["_import_last_file"] = filename
        st.session_state.pop("_import_done_new", None)
        st.session_state.pop("_import_done_replace", None)
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem;padding:0.75rem 1rem;
                background:var(--bg-card-alt);border-radius:0.5rem;border:1px solid var(--border);">
        <span style="color:var(--accent-light);">📁</span>
        <span style="font-size:0.875rem;color:var(--text-body);font-weight:500;">File:
            <code style="color:var(--accent-light);background:var(--bg-code);padding:0.15rem 0.4rem;
                         border-radius:0.25rem;font-size:0.85em;">{filename}</code>
        </span>
    </div>
    """, unsafe_allow_html=True)

    try:
        xls = pd.ExcelFile(uploaded_file)
    except Exception as e:
        st.error(f"❌ Không đọc được file: {e}")
        return

    # ── Step 2: Auto-detect compatible sheets ──
    st.markdown(section_title("Phát hiện sheet dữ liệu", "🔍"), unsafe_allow_html=True)

    with st.spinner("⏳ Đang quét các sheet..."):
        compatible = _detect_compatible_sheets(xls)

    if not compatible:
        st.markdown(info_banner(
            f"Không tìm thấy sheet nào có cấu trúc phù hợp. "
            f"Cần tối thiểu <strong>14 cột bắt buộc</strong>: "
            f"<code>{'</code>, <code>'.join(_REQUIRED_COLS)}</code>",
            "error"
        ), unsafe_allow_html=True)
        # Show all sheets and their columns for debugging
        with st.expander("📋 Xem danh sách sheet trong file"):
            for sheet_name in xls.sheet_names:
                try:
                    hdf = pd.read_excel(xls, sheet_name=sheet_name, nrows=0, engine="openpyxl")
                    st.markdown(f"**{sheet_name}** — {len(hdf.columns)} cột: `{'`, `'.join(hdf.columns[:15])}`{'...' if len(hdf.columns) > 15 else ''}")
                except Exception:
                    st.markdown(f"**{sheet_name}** — ❌ Không đọc được")
        return

    # Show compatible sheet info
    if len(compatible) == 1:
        sel_info = compatible[0]
        st.markdown(info_banner(
            f"Tự động phát hiện sheet <strong>{sel_info['sheet_name']}</strong> "
            f"({len(sel_info['matched_cols'])}/{len(_SCHEMA_COLS)} cột khớp)",
            "success"
        ), unsafe_allow_html=True)
    else:
        st.markdown(info_banner(
            f"Phát hiện <strong>{len(compatible)}</strong> sheet có cấu trúc phù hợp.",
            "info"
        ), unsafe_allow_html=True)

    # Dropdown if multiple
    sheet_names = [c["sheet_name"] for c in compatible]
    selected_sheet = st.selectbox(
        "📄 Chọn sheet:",
        sheet_names,
        key="_import_sheet_select",
    )
    sel_info = next(c for c in compatible if c["sheet_name"] == selected_sheet)

    # Column validation report
    with st.expander(f"📊 Chi tiết cột — {len(sel_info['matched_cols'])} khớp, {len(sel_info['extra_cols'])} thừa"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**✅ Cột khớp schema:**")
            st.code(", ".join(sel_info["matched_cols"]))
        with col2:
            if sel_info["extra_cols"]:
                st.markdown("**⚠️ Cột thừa (bỏ qua):**")
                st.code(", ".join(sel_info["extra_cols"]))
            else:
                st.markdown("**✅ Không có cột thừa**")

    # ── Step 3: Read & transform data ──
    st.markdown(divider(), unsafe_allow_html=True)
    st.markdown(section_title("Đọc & kiểm tra dữ liệu", "📖"), unsafe_allow_html=True)

    try:
        with st.spinner("⏳ Đang đọc và chuẩn hóa dữ liệu..."):
            df_raw = pd.read_excel(xls, sheet_name=selected_sheet, engine="openpyxl")
            df = _transform_dataframe(df_raw.copy(), filename)
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu: {e}")
        return

    st.markdown(info_banner(
        f"Đọc được <strong>{len(df):,}</strong> dòng, <strong>{len(df.columns)}</strong> cột",
        "success"
    ), unsafe_allow_html=True)

    # ── Step 4: Row-level validation ──
    valid_df, invalid_df, issues = _validate_rows(df)

    if not invalid_df.empty:
        # Build issue summary
        issue_details = ", ".join([f"`{col}`: {n} dòng" for col, n in issues])
        st.markdown(info_banner(
            f"Phát hiện <strong>{len(invalid_df):,}</strong> dòng không hợp lệ "
            f"(thiếu dữ liệu hoặc sai định dạng). Đã loại khỏi tập dữ liệu upload.<br>"
            f"<small style='color:var(--text-secondary);'>Chi tiết: {issue_details}</small>",
            "warning"
        ), unsafe_allow_html=True)

        with st.expander(f"🚫 Xem {len(invalid_df):,} dòng không hợp lệ"):
            paginated_dataframe(invalid_df, key_prefix="_import_invalid")

    if valid_df.empty:
        st.markdown(info_banner("Không còn dữ liệu hợp lệ sau khi kiểm tra.", "error"), unsafe_allow_html=True)
        return

    # ── Step 5: Data summary ──
    combos = valid_df[["nam_qt", "thang_qt", "ma_cskcb"]].drop_duplicates()
    summary_headers = ["Kỳ", "Mã CSKCB", "Số dòng", "Tổng chi"]
    summary_rows = []
    for _, row in combos.iterrows():
        subset = valid_df[
            (valid_df["nam_qt"] == row["nam_qt"]) &
            (valid_df["thang_qt"] == row["thang_qt"]) &
            (valid_df["ma_cskcb"] == row["ma_cskcb"])
        ]
        summary_rows.append([
            f"{int(row['thang_qt']):02d}/{int(row['nam_qt'])}",
            str(row["ma_cskcb"]),
            f"{len(subset):,}",
            f"{subset['t_tongchi'].sum():,.0f} VNĐ",
        ])
    st.markdown(data_table(summary_headers, summary_rows, ["c", "c", "r", "r"]), unsafe_allow_html=True)

    # ── Step 6: Check duplicates ──
    st.markdown(divider(), unsafe_allow_html=True)
    st.markdown(section_title("Kiểm tra trùng lặp", "🔍"), unsafe_allow_html=True)

    client = get_client()

    with st.spinner("⏳ Đang kiểm tra trùng lặp với BigQuery..."):
        dup_df = _check_duplicates(client, valid_df)

    # Split into new vs duplicate
    if not dup_df.empty:
        dup_keys = set(dup_df[_ROW_KEY_COLS].apply(tuple, axis=1))
        new_df = valid_df[~valid_df[_ROW_KEY_COLS].apply(tuple, axis=1).isin(dup_keys)].copy()
    else:
        new_df = valid_df.copy()

    # ── Step 7: Lookup code validation ──
    with st.spinner("⏳ Đang kiểm tra mã khoa và mã CSKCB..."):
        lookup_warnings = _check_lookup_codes(client, valid_df)

    if lookup_warnings:
        for w in lookup_warnings:
            st.markdown(info_banner(w, "warning"), unsafe_allow_html=True)

    # ── Step 8: Display Table 1 — New records ──
    if not new_df.empty:
        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title(
            f"Dữ liệu mới — {len(new_df):,} record", "✅"
        ), unsafe_allow_html=True)
        st.markdown(info_banner(
            f"<strong>{len(new_df):,}</strong> dòng chưa có trên BigQuery, sẵn sàng tải lên.",
            "success"
        ), unsafe_allow_html=True)

        paginated_dataframe(new_df, key_prefix="_import_new")

        # Upload button (disabled after successful upload)
        already_uploaded = st.session_state.get("_import_done_new", False)
        if already_uploaded:
            st.markdown(info_banner(
                "✅ Dữ liệu mới đã được tải lên thành công!", "success"
            ), unsafe_allow_html=True)
        if st.button(
            "✅ Xác nhận tải lên", type="primary",
            key="_import_upload_new_btn",
            disabled=already_uploaded,
        ):
            _do_upload(client, new_df, upload_type="new")

    # ── Step 9: Display Table 2 — Duplicate records ──
    if not dup_df.empty:
        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title(
            f"Dữ liệu trùng — {len(dup_df):,} record", "🔄"
        ), unsafe_allow_html=True)

        # Duplicate summary
        dup_summary = dup_df.groupby(["nam_qt", "thang_qt", "ma_cskcb"]).size().reset_index(name="so_dong")
        st.markdown(info_banner(
            f"<strong>{len(dup_df):,}</strong> dòng đã tồn tại trên BigQuery "
            f"(trùng theo composite key: <code>{'</code> + <code>'.join(_ROW_KEY_COLS)}</code>)",
            "warning"
        ), unsafe_allow_html=True)

        for _, r in dup_summary.iterrows():
            st.markdown(card_list_item(
                f"{int(r['thang_qt']):02d}/{int(r['nam_qt'])} | CSKCB: {r['ma_cskcb']}",
                f"{r['so_dong']:,} dòng trùng",
                "Trùng",
                "orange",
            ), unsafe_allow_html=True)

        paginated_dataframe(dup_df, key_prefix="_import_dup")

        # Replace button (disabled after successful replace)
        already_replaced = st.session_state.get("_import_done_replace", False)
        if already_replaced:
            st.markdown(info_banner(
                "✅ Hồ sơ trùng đã được thay thế thành công!", "success"
            ), unsafe_allow_html=True)
        if st.button(
            "🔄 Xác nhận thay thế hồ sơ", type="secondary",
            key="_import_replace_btn",
            disabled=already_replaced,
        ):
            with st.spinner("🗑️ Đang xóa dữ liệu trùng cũ trên BigQuery..."):
                deleted = _delete_duplicates_from_bq(client, dup_df)
            st.markdown(info_banner(
                f"Đã xóa <strong>{deleted:,}</strong> hồ sơ cũ. Đang upload dữ liệu thay thế...",
                "info"
            ), unsafe_allow_html=True)
            _do_upload(client, dup_df, upload_type="replace")

    # ── No data at all ──
    if new_df.empty and dup_df.empty:
        st.markdown(info_banner("Không có dữ liệu hợp lệ để hiển thị.", "info"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def render():
    """Render trang Quản lý số liệu với 3 tab."""

    st.markdown(page_header(
        "Quản lý số liệu",
        "Tổng hợp · Quản lý · Import dữ liệu thanh toán BHYT",
        "📊"
    ), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📈 Số liệu tổng hợp",
        "📋 Quản lý số liệu",
        "📥 Import",
    ])

    with tab1:
        _render_tab_overview()

    with tab2:
        _render_tab_manage()

    with tab3:
        _render_tab_import()

    # ── Persist active tab across st.rerun() (e.g. theme toggle) ──
    # Uses browser sessionStorage to track the active tab index.
    # On rerun, JS restores the previously active tab by clicking it.
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        const doc = window.parent.document;
        const STORAGE_KEY = '_ov_active_tab';

        // Restore saved tab on load
        const savedIdx = parseInt(sessionStorage.getItem(STORAGE_KEY) || '0', 10);
        if (savedIdx > 0) {
            const tabs = doc.querySelectorAll('[data-baseweb="tab"]');
            if (tabs && tabs.length > savedIdx) {
                const currentActive = doc.querySelector('[data-baseweb="tab"][aria-selected="true"]');
                const targetTab = tabs[savedIdx];
                if (currentActive !== targetTab) {
                    targetTab.click();
                }
            }
        }

        // Watch for tab clicks and save the active index
        function watchTabs() {
            const tabs = doc.querySelectorAll('[data-baseweb="tab"]');
            tabs.forEach((tab, idx) => {
                if (!tab.dataset._tabWatch) {
                    tab.dataset._tabWatch = '1';
                    tab.addEventListener('click', () => {
                        sessionStorage.setItem(STORAGE_KEY, String(idx));
                    });
                }
            });
        }

        watchTabs();
        const obs = new MutationObserver(watchTabs);
        obs.observe(doc.body, { childList: true, subtree: true });
    })();
    </script>
    """, height=0)

