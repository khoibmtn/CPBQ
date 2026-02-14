"""
views/overview.py - Trang Quản lý số liệu
============================================
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


def _render_tab_manage():
    """Render tab Quản lý số liệu."""

    st.markdown("#### 📋 Thống kê dữ liệu trên BigQuery")

    try:
        total_rows = _load_total_rows()
        summary = _load_data_summary()
    except Exception as e:
        st.error(f"❌ Lỗi truy vấn BigQuery: {e}")
        return

    # ── Metrics ──
    if summary.empty:
        st.info("ℹ️ Chưa có dữ liệu trên BigQuery.")
        return

    n_years = summary["nam_qt"].nunique()
    n_months = summary[["nam_qt", "thang_qt"]].drop_duplicates().shape[0]

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("📊 Tổng số dòng", f"{total_rows:,}")
    with mc2:
        st.metric("📅 Số kỳ (tháng)", f"{n_months}")
    with mc3:
        st.metric("🗓️ Số năm", f"{n_years}")

    st.markdown("---")

    # ── Data summary table ──
    st.markdown("##### 📊 Chi tiết theo kỳ")

    display_df = summary.copy()
    display_df["thang_nam"] = display_df.apply(
        lambda r: f"{int(r['thang_qt']):02d}/{int(r['nam_qt'])}", axis=1
    )
    display_df["tong_chi_fmt"] = display_df["tong_chi"].apply(
        lambda v: f"{v:,.0f}" if pd.notna(v) else "—"
    )
    display_df["so_dong_fmt"] = display_df["so_dong"].apply(lambda v: f"{v:,}")

    # Build HTML table
    html = """
    <style>
    .mgmt-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
    }
    .mgmt-table th {
        background: #1e293b;
        color: white;
        padding: 10px 14px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #334155;
    }
    .mgmt-table td {
        padding: 8px 14px;
        border: 1px solid #e2e8f0;
    }
    .mgmt-table tr:nth-child(even) { background: #f8fafc; }
    .mgmt-table tr:hover { background: rgba(14,165,233,0.08); }
    .mgmt-table .num { text-align: right; }
    .mgmt-table .ctr { text-align: center; }
    </style>
    <table class="mgmt-table">
    <thead><tr>
        <th>Kỳ</th>
        <th>Mã CSKCB</th>
        <th>Số dòng</th>
        <th>Tổng chi (VNĐ)</th>
        <th>File nguồn</th>
    </tr></thead>
    <tbody>
    """
    for _, r in display_df.iterrows():
        html += f"""<tr>
            <td class="ctr">{r['thang_nam']}</td>
            <td class="ctr">{r['ma_cskcb']}</td>
            <td class="num">{r['so_dong_fmt']}</td>
            <td class="num">{r['tong_chi_fmt']}</td>
            <td>{r['source_files'] or '—'}</td>
        </tr>"""
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    # ── Xóa dữ liệu ──
    st.markdown("---")
    st.markdown("##### 🗑️ Xóa dữ liệu theo kỳ")
    st.caption("⚠️ Thao tác này không thể hoàn tác. Hãy cẩn thận!")

    # Build options for deletion
    options = []
    for _, r in display_df.iterrows():
        label = f"{r['thang_nam']} | CSKCB: {r['ma_cskcb']} | {r['so_dong_fmt']} dòng"
        options.append({
            "label": label,
            "nam_qt": int(r["nam_qt"]),
            "thang_qt": int(r["thang_qt"]),
            "ma_cskcb": r["ma_cskcb"],
            "so_dong": int(r["so_dong"]),
        })

    selected_labels = st.multiselect(
        "Chọn kỳ muốn xóa:",
        [o["label"] for o in options],
        key="_mgmt_delete_select",
    )

    if selected_labels:
        selected_opts = [o for o in options if o["label"] in selected_labels]
        total_del = sum(o["so_dong"] for o in selected_opts)

        st.warning(f"⚠️ Bạn đang chọn xóa **{total_del:,}** dòng dữ liệu.")

        col_del1, col_del2, _ = st.columns([1, 1, 3])
        with col_del1:
            confirm_text = st.text_input(
                "Nhập `XÓA` để xác nhận:",
                key="_mgmt_delete_confirm",
            )
        with col_del2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Xóa dữ liệu", type="primary", key="_mgmt_delete_btn"):
                if confirm_text != "XÓA":
                    st.error("❌ Nhập đúng `XÓA` để xác nhận.")
                else:
                    client = get_client()
                    progress = st.progress(0)
                    for i, opt in enumerate(selected_opts):
                        delete_q = f"""
                            DELETE FROM `{FULL_TABLE_ID}`
                            WHERE nam_qt = {opt['nam_qt']}
                              AND thang_qt = {opt['thang_qt']}
                              AND ma_cskcb = '{opt['ma_cskcb']}'
                        """
                        client.query(delete_q).result()
                        progress.progress((i + 1) / len(selected_opts))

                    st.success(f"✅ Đã xóa {total_del:,} dòng dữ liệu!")
                    # Clear caches
                    _load_data_summary.clear()
                    _load_total_rows.clear()
                    _load_overview_data.clear()
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

# Schema and key columns (from upload_to_bigquery.py)
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

_ROW_KEY_COLS = ["ma_cskcb", "ma_bn", "ma_loaikcb", "ngay_vao", "ngay_ra"]


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
    # Lowercase all column names
    df.columns = [c.lower().strip() for c in df.columns]

    # Date columns: YYYYMMDD int → date
    for col in ["ngay_sinh", "gt_the_tu", "gt_the_den"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_date_int)

    # Datetime columns: string → datetime
    for col in ["ngay_vao", "ngay_ra"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_datetime_str)

    # String columns: ensure str type
    str_cols = ["ma_bn", "ma_the", "ma_dkbd", "ma_benh", "ma_benhkhac",
                "ma_noi_chuyen", "ma_khoa", "ma_khuvuc", "ma_cskcb",
                "giam_dinh", "ho_ten", "dia_chi"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) and x != "" else None)
            df[col] = df[col].replace("nan", None)

    # Float columns
    float_cols = ["t_tongchi", "t_xn", "t_cdha", "t_thuoc", "t_mau",
                  "t_pttt", "t_vtyt", "t_dvkt_tyle", "t_thuoc_tyle",
                  "t_vtyt_tyle", "t_kham", "t_giuong", "t_vchuyen",
                  "t_bntt", "t_bhtt", "t_ngoaids", "t_xuattoan",
                  "t_nguonkhac", "t_datuyen", "t_vuottran"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Int columns
    int_cols = ["stt", "gioi_tinh", "ma_lydo_vvien", "so_ngay_dtri",
                "ket_qua_dtri", "tinh_trang_rv", "nam_qt", "thang_qt",
                "ma_loaikcb", "noi_ttoan"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add metadata columns
    df["upload_timestamp"] = datetime.utcnow()
    df["source_file"] = source_filename

    return df


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

    # Merge chính xác theo composite key
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


def _render_tab_import():
    """Render tab Import dữ liệu."""

    st.markdown("#### 📥 Import dữ liệu Excel lên BigQuery")
    st.caption(
        f"Upload file Excel chứa dữ liệu thanh toán BHYT. "
        f"Sheet mặc định: **{SHEET_NAME}** · "
        f"Target: `{FULL_TABLE_ID}`"
    )

    # ── File uploader ──
    uploaded_file = st.file_uploader(
        "Chọn file Excel (.xlsx, .xls)",
        type=["xlsx", "xls"],
        key="_import_file_uploader",
    )

    if uploaded_file is None:
        st.info("ℹ️ Chọn file Excel để bắt đầu.")
        return

    # ── Read Excel ──
    filename = uploaded_file.name
    st.markdown(f"📁 **File:** `{filename}`")

    try:
        xls = pd.ExcelFile(uploaded_file)
        sheets = xls.sheet_names
    except Exception as e:
        st.error(f"❌ Không đọc được file: {e}")
        return

    # Sheet selection
    # Try to auto-select SHEET_NAME
    default_sheet_idx = 0
    sheets_lower = [s.lower() for s in sheets]
    if SHEET_NAME.lower() in sheets_lower:
        default_sheet_idx = sheets_lower.index(SHEET_NAME.lower())

    selected_sheet = st.selectbox(
        "📄 Chọn sheet:",
        sheets,
        index=default_sheet_idx,
        key="_import_sheet_select",
    )

    # Initialize session state for import workflow
    if "_import_state" not in st.session_state:
        st.session_state._import_state = "preview"  # preview → checking → ready → uploading → done

    # ── Button: Đọc & xem trước ──
    if st.button("📖 Đọc & xem trước dữ liệu", key="_import_preview_btn"):
        st.session_state._import_state = "preview"
        st.session_state._import_df = None

    try:
        with st.spinner("⏳ Đang đọc file Excel..."):
            df_raw = pd.read_excel(xls, sheet_name=selected_sheet, engine="openpyxl")
            df = _transform_dataframe(df_raw.copy(), filename)

        st.session_state._import_df = df
        st.success(f"✅ Đọc được **{len(df):,}** dòng, **{len(df.columns)}** cột từ sheet '{selected_sheet}'")
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu: {e}")
        return

    df = st.session_state.get("_import_df")
    if df is None:
        return

    # ── Tóm tắt dữ liệu ──
    st.markdown("##### 📋 Tóm tắt dữ liệu")
    combos = df[["nam_qt", "thang_qt", "ma_cskcb"]].drop_duplicates()

    summary_rows = []
    for _, row in combos.iterrows():
        subset = df[(df["nam_qt"] == row["nam_qt"]) &
                     (df["thang_qt"] == row["thang_qt"]) &
                     (df["ma_cskcb"] == row["ma_cskcb"])]
        summary_rows.append({
            "Kỳ": f"{int(row['thang_qt']):02d}/{int(row['nam_qt'])}",
            "Mã CSKCB": row["ma_cskcb"],
            "Số dòng": f"{len(subset):,}",
            "Tổng chi": f"{subset['t_tongchi'].sum():,.0f} VNĐ",
        })

    st.table(pd.DataFrame(summary_rows))

    # ── Xem trước dữ liệu ──
    with st.expander("🔍 Xem trước 20 dòng đầu"):
        preview_cols = ["stt", "ma_bn", "ho_ten", "ma_cskcb", "ma_loaikcb",
                        "nam_qt", "thang_qt", "t_tongchi", "t_bhtt", "t_bntt"]
        available_cols = [c for c in preview_cols if c in df.columns]
        st.dataframe(df[available_cols].head(20), use_container_width=True, hide_index=True)

    # ── Kiểm tra trùng lặp & Upload ──
    st.markdown("---")
    st.markdown("##### 🚀 Upload lên BigQuery")

    if st.button("🔍 Kiểm tra trùng lặp & Upload", type="primary", key="_import_check_btn"):
        client = get_client()

        with st.spinner("⏳ Đang kiểm tra trùng lặp..."):
            dup_df = _check_duplicates(client, df)

        if not dup_df.empty:
            # Thống kê trùng
            dup_summary = dup_df.groupby(["nam_qt", "thang_qt", "ma_cskcb"]).size().reset_index(name="so_dong")
            st.warning(f"⚠️ Phát hiện **{len(dup_df):,}/{len(df):,}** dòng đã tồn tại trên BigQuery:")
            for _, r in dup_summary.iterrows():
                st.markdown(
                    f"  - {int(r['thang_qt']):02d}/{int(r['nam_qt'])} "
                    f"| CSKCB: {r['ma_cskcb']} | **{r['so_dong']:,}** dòng trùng"
                )

            new_count = len(df) - len(dup_df)
            st.info(f"ℹ️ Dòng mới (chưa có trên BQ): **{new_count:,}**")

            # Options for duplicate handling
            dup_action = st.radio(
                "Chọn cách xử lý:",
                [
                    "Bỏ qua phần trùng, chỉ upload phần mới",
                    "Upload tất cả (cho phép trùng)",
                    "Xóa dữ liệu trùng cũ rồi upload lại tất cả",
                    "Hủy",
                ],
                key="_import_dup_action",
            )

            if st.button("✅ Thực hiện", key="_import_exec_btn"):
                if dup_action == "Hủy":
                    st.info("❌ Đã hủy upload.")
                    return

                upload_df = df.copy()

                if dup_action == "Bỏ qua phần trùng, chỉ upload phần mới":
                    dup_keys = set(dup_df[_ROW_KEY_COLS].apply(tuple, axis=1))
                    upload_df = df[~df[_ROW_KEY_COLS].apply(tuple, axis=1).isin(dup_keys)]
                    if len(upload_df) == 0:
                        st.info("ℹ️ Không còn dữ liệu mới để upload.")
                        return

                elif dup_action == "Xóa dữ liệu trùng cũ rồi upload lại tất cả":
                    with st.spinner("🗑️ Đang xóa dữ liệu trùng cũ..."):
                        dup_groups = dup_df.groupby(["nam_qt", "thang_qt", "ma_cskcb"])
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
                        st.success("✅ Đã xóa dữ liệu trùng cũ.")

                # Upload
                _do_upload(client, upload_df)

        else:
            st.success("✅ Không phát hiện trùng lặp. Đang upload...")
            _do_upload(client, df)


def _do_upload(client, df: pd.DataFrame):
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
    st.success(
        f"🎉 Upload thành công! **{len(df):,}** dòng đã được thêm. "
        f"Tổng số dòng trên BigQuery: **{table.num_rows:,}**"
    )

    # Clear caches
    _load_data_summary.clear()
    _load_total_rows.clear()
    _load_overview_data.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def render():
    """Render trang Quản lý số liệu với 3 tab."""

    st.markdown("""
    <div class="main-header">
        <h1>📊 Quản lý số liệu</h1>
        <p>Tổng hợp · Quản lý · Import dữ liệu thanh toán BHYT</p>
    </div>
    """, unsafe_allow_html=True)

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
