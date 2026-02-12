"""
pages/overview.py - Trang Tổng quan
=====================================
Bảng pivot: tháng × CSKCB × nội/ngoại trú
"""

import streamlit as st
import pandas as pd
from bq_helper import run_query
from config import PROJECT_ID, DATASET_ID, VIEW_ID


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


def render():
    """Render trang Tổng quan."""

    st.markdown("""
    <div class="main-header">
        <h1>📊 Tổng quan thanh toán BHYT</h1>
        <p>Bảng tổng hợp theo tháng · Nội trú / Ngoại trú · Cơ sở KCB</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters ──
    years = _get_available_years()
    if not years:
        st.warning("⚠️ Chưa có dữ liệu trong database.")
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
        st.info(f"ℹ️ Không có dữ liệu cho năm {selected_year}.")
        return

    # ── Build & display pivot table ──
    pivot, ngoai_names, noi_names = _build_pivot_table(data, metric)

    if pivot.empty:
        st.info("ℹ️ Không có dữ liệu để hiển thị.")
        return

    # Hiển thị summary metrics
    total_row = pivot.iloc[-1]
    mcol1, mcol2, mcol3 = st.columns(3)
    unit = " VNĐ" if metric == "tong_chi" else " lượt"
    with mcol1:
        val = total_row.get("Ngoại trú|Tổng", 0)
        st.metric("Tổng Ngoại trú", f"{val:,.0f}{unit}")
    with mcol2:
        val = total_row.get("Nội trú|Tổng", 0)
        st.metric("Tổng Nội trú", f"{val:,.0f}{unit}")
    with mcol3:
        val = total_row.get("TỔNG CỘNG", 0)
        st.metric("Tổng cộng", f"{val:,.0f}{unit}")

    st.markdown("---")

    # ── Render pivot table as HTML ──
    _render_html_table(pivot, ngoai_names, noi_names, metric)

    # ── Raw data expander ──
    with st.expander("🔍 Xem dữ liệu chi tiết"):
        st.dataframe(data, use_container_width=True, hide_index=True)


def _render_html_table(pivot: pd.DataFrame, ngoai_names: list, noi_names: list, metric: str):
    """Render bảng pivot dạng HTML với multi-level headers."""

    fmt = lambda v: f"{v:,.0f}" if pd.notna(v) and v != 0 else ""

    # Build column groups
    ngoai_cols = [f"Ngoại trú|{n}" for n in ngoai_names] + ["Ngoại trú|Tổng"]
    noi_cols = [f"Nội trú|{n}" for n in noi_names] + ["Nội trú|Tổng"]

    ngoai_span = len(ngoai_cols)
    noi_span = len(noi_cols)

    # CSS with dark mode support
    css = """
    <style>
    /* ── CSS Custom Properties ── */
    :root {
        --pv-bg: #ffffff;
        --pv-text: #1e293b;
        --pv-border: #e2e8f0;
        --pv-first-col-bg: #f8fafc;
        --pv-col-tong-bg: #f0f9ff;
        --pv-col-tong-text: #1e293b;
        --pv-even-bg: #f8fafc;
        --pv-odd-bg: #ffffff;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --pv-bg: #0e1117;
            --pv-text: #e2e8f0;
            --pv-border: #334155;
            --pv-first-col-bg: rgba(51,65,85,0.5);
            --pv-col-tong-bg: rgba(14,165,233,0.12);
            --pv-col-tong-text: #e2e8f0;
            --pv-even-bg: rgba(51,65,85,0.25);
            --pv-odd-bg: transparent;
        }
    }

    .pivot-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        margin-top: 0.5rem;
        background: var(--pv-bg);
        color: var(--pv-text);
    }
    .pivot-table th, .pivot-table td {
        padding: 8px 12px;
        border: 1px solid var(--pv-border);
    }
    .pivot-table th {
        font-weight: 600;
        text-align: center;
        color: white;
    }
    .pivot-table td {
        text-align: right;
        color: var(--pv-text);
    }
    .pivot-table td:first-child {
        text-align: center;
        font-weight: 600;
        background-color: var(--pv-first-col-bg);
    }
    .group-ngoai { background-color: #2563eb; }
    .group-noi  { background-color: #ea580c; }
    .group-tong { background-color: #0f172a; }
    .sub-header { background-color: #334155; font-size: 12px; }
    .col-tong {
        background-color: var(--pv-col-tong-bg);
        color: var(--pv-col-tong-text);
        font-weight: 600;
    }
    .row-total {
        background-color: #1e293b !important;
        color: white !important;
        font-weight: 700;
    }
    .row-total td {
        background-color: #1e293b !important;
        color: white !important;
    }
    .row-even { background-color: var(--pv-even-bg); }
    .row-odd  { background-color: var(--pv-odd-bg);  }
    </style>
    """

    # Table header row 1: group names
    html = css + '<table class="pivot-table">'
    html += "<thead>"
    html += '<tr>'
    html += '<th class="group-tong" rowspan="2">Tháng</th>'
    if ngoai_span > 0:
        html += f'<th class="group-ngoai" colspan="{ngoai_span}">🔵 Ngoại trú</th>'
    if noi_span > 0:
        html += f'<th class="group-noi" colspan="{noi_span}">🟠 Nội trú</th>'
    html += '<th class="group-tong" rowspan="2">TỔNG CỘNG</th>'
    html += '</tr>'

    # Table header row 2: sub-columns
    html += '<tr>'
    for col in ngoai_cols:
        label = col.split("|")[1]
        html += f'<th class="sub-header">{label}</th>'
    for col in noi_cols:
        label = col.split("|")[1]
        html += f'<th class="sub-header">{label}</th>'
    html += '</tr>'
    html += "</thead>"

    # Table body
    html += "<tbody>"
    for idx, row in pivot.iterrows():
        is_total = row["Tháng"] == "TỔNG NĂM"
        row_class = "row-total" if is_total else ("row-even" if idx % 2 == 0 else "row-odd")

        html += f'<tr class="{row_class}">'
        html += f'<td>{row["Tháng"]}</td>'

        for col in ngoai_cols:
            is_subtotal = col.endswith("|Tổng")
            td_class = "col-tong" if is_subtotal and not is_total else ""
            html += f'<td class="{td_class}">{fmt(row.get(col, 0))}</td>'

        for col in noi_cols:
            is_subtotal = col.endswith("|Tổng")
            td_class = "col-tong" if is_subtotal and not is_total else ""
            html += f'<td class="{td_class}">{fmt(row.get(col, 0))}</td>'

        tong_class = "col-tong" if not is_total else ""
        html += f'<td class="{tong_class}">{fmt(row.get("TỔNG CỘNG", 0))}</td>'
        html += '</tr>'

    html += "</tbody></table>"

    st.markdown(html, unsafe_allow_html=True)
