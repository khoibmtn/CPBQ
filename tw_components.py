"""
tw_components.py – Streamlit component library (inline CSS, no Tailwind CDN)
=============================================================================
Reusable HTML helpers that render via st.markdown(unsafe_allow_html=True).
Uses inline CSS styles for reliability (Streamlit strips <script> tags).
All functions return HTML strings — no Streamlit widget calls inside.
"""

import streamlit as st
from typing import List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CORE: CSS INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_tailwind():
    """Inject Google Fonts. Called once at app startup."""
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)


def override_streamlit_widgets():
    """CSS overrides to restyle Streamlit widgets to dark theme."""
    st.markdown("""
    <style>
    html, body, [class*="st-"] {
        font-family: 'Inter', system-ui, sans-serif;
    }

    /* ── Disable Streamlit rerun fade ── */
    [data-stale="true"], .stale-element,
    .element-container, .stMarkdown, .stDataFrame,
    [data-testid="stVerticalBlockBorderWrapper"] {
        opacity: 1 !important;
        transition: none !important;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    /* ── Overall page background ── */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }
    .stMainBlockContainer {
        max-width: 1200px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(51,65,85,0.5);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stHorizontalBlock {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    [data-testid="stSidebar"] hr {
        margin-left: 1rem;
        margin-right: 1rem;
        border-color: rgba(51,65,85,0.5);
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] label {
        color: #94a3b8 !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: rgba(148,163,184,0.5) !important;
    }

    /* ── Sidebar collapse/expand buttons ── */
    button[data-testid="stBaseButton-headerNoPadding"] {
        overflow: hidden; position: relative;
        width: 2.2rem; height: 2.2rem; min-height: unset;
        padding: 0 !important;
    }
    button[data-testid="stBaseButton-headerNoPadding"] span {
        font-size: 0 !important; visibility: hidden;
    }
    button[data-testid="stBaseButton-headerNoPadding"]::after {
        visibility: visible; position: absolute;
        top: 50%; left: 50%; transform: translate(-50%, -50%);
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"] {
        margin-left: 0.5rem;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"]::after {
        content: '✕'; font-size: 1.1rem; color: #94a3b8;
    }
    button[data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"] button {
        overflow: hidden !important; position: relative;
        width: 2.2rem; height: 2.2rem; min-height: unset;
        padding: 0 !important;
    }
    button[data-testid="stExpandSidebarButton"] span,
    [data-testid="stSidebarCollapsedControl"] button span {
        font-size: 0 !important; visibility: hidden;
    }
    button[data-testid="stExpandSidebarButton"]::after,
    [data-testid="stSidebarCollapsedControl"] button::after {
        content: '☰'; font-size: 1.3rem; color: #94a3b8;
        visibility: visible; position: absolute;
        top: 50%; left: 50%; transform: translate(-50%, -50%);
    }

    /* ── Sidebar menu buttons ── */
    [data-testid="stSidebar"] .stElementContainer:has(.stButton) {
        padding-left: 0 !important; padding-right: 0 !important;
    }
    [data-testid="stSidebar"] .stButton { margin-left: 0; margin-right: 0; }
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important; text-align: left;
        padding: 0.75rem 1.2rem; border-radius: 0;
        border: none !important; font-size: 0.95rem;
        font-family: 'Inter', sans-serif;
        cursor: pointer; transition: all 0.2s ease;
        margin-bottom: 0;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: transparent !important; color: #94a3b8 !important;
        font-weight: 500; box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: rgba(59,130,246,0.08) !important;
        color: #e2e8f0 !important;
        box-shadow: -11px 0 0 0 rgba(59,130,246,0.08), 11px 0 0 0 rgba(59,130,246,0.08) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: rgba(59,130,246,0.15) !important;
        color: #60a5fa !important; font-weight: 600;
        border-left: 3px solid #3b82f6 !important;
        box-shadow: -11px 0 0 0 rgba(59,130,246,0.15), 11px 0 0 0 rgba(59,130,246,0.15) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: rgba(59,130,246,0.2) !important;
        box-shadow: -11px 0 0 0 rgba(59,130,246,0.2), 11px 0 0 0 rgba(59,130,246,0.2) !important;
    }
    [data-testid="stSidebar"] .stButton > button:focus {
        outline: none !important;
    }

    /* ── Restyle Streamlit native widgets ── */

    /* Selectbox */
    [data-testid="stSelectbox"] label {
        color: #94a3b8 !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stSelectbox"] > div > div {
        background: rgba(30,41,59,0.8) !important;
        border: 1px solid rgba(51,65,85,0.8) !important;
        border-radius: 0.5rem !important; color: #e2e8f0 !important;
    }

    /* Text input */
    [data-testid="stTextInput"] label {
        color: #94a3b8 !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stTextInput"] input {
        background: rgba(30,41,59,0.8) !important;
        border: 1px solid rgba(51,65,85,0.8) !important;
        border-radius: 0.5rem !important; color: #e2e8f0 !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
    }

    /* Multiselect */
    [data-testid="stMultiSelect"] label {
        color: #94a3b8 !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stMultiSelect"] > div > div {
        background: rgba(30,41,59,0.8) !important;
        border: 1px solid rgba(51,65,85,0.8) !important;
        border-radius: 0.5rem !important;
    }

    /* Buttons (main area) */
    .stMainBlockContainer .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important; border: none !important;
        border-radius: 0.5rem !important; font-weight: 600;
        padding: 0.5rem 1.25rem; transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
    }
    .stMainBlockContainer .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(59,130,246,0.4) !important;
        transform: translateY(-1px);
    }
    .stMainBlockContainer .stButton > button[kind="secondary"] {
        background: rgba(30,41,59,0.8) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(51,65,85,0.8) !important;
        border-radius: 0.5rem !important; font-weight: 500;
        transition: all 0.2s ease;
    }
    .stMainBlockContainer .stButton > button[kind="secondary"]:hover {
        background: rgba(51,65,85,0.6) !important;
        color: #e2e8f0 !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] label {
        color: #94a3b8 !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(30,41,59,0.5) !important;
        border: 2px dashed rgba(51,65,85,0.8) !important;
        border-radius: 0.75rem !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(59,130,246,0.5) !important;
        background: rgba(59,130,246,0.05) !important;
    }

    /* Radio buttons */
    [data-testid="stRadio"] label { color: #94a3b8 !important; }
    [data-testid="stRadio"] p { color: #cbd5e1 !important; }

    /* Tabs */
    [data-testid="stTabs"] button[data-baseweb="tab"] {
        color: #64748b !important; font-weight: 500;
        border-bottom: 2px solid transparent !important;
        transition: all 0.2s ease;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        color: #60a5fa !important;
        border-bottom: 2px solid #3b82f6 !important;
        font-weight: 600;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"]:hover {
        color: #93c5fd !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: rgba(30,41,59,0.5) !important;
        border: 1px solid rgba(51,65,85,0.5) !important;
        border-radius: 0.75rem !important;
    }
    [data-testid="stExpander"] summary span {
        color: #94a3b8 !important; font-weight: 500;
    }

    /* Metric cards (override default) */
    [data-testid="stMetric"] {
        background: transparent !important;
        padding: 0 !important; border-left: none !important;
    }

    /* Data editor / DataFrame */
    [data-testid="stDataFrame"], .stDataFrame {
        border-radius: 0.75rem !important; overflow: hidden;
    }

    /* Spinner */
    .stSpinner > div { color: #60a5fa !important; }

    /* Alert boxes */
    [data-testid="stAlert"] {
        background: rgba(30,41,59,0.6) !important;
        border: 1px solid rgba(51,65,85,0.5) !important;
        border-radius: 0.75rem !important;
        color: #cbd5e1 !important;
    }

    /* Progress bar */
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #3b82f6, #0ea5e9) !important;
        border-radius: 0.25rem;
    }

    /* Caption & text */
    .stCaption { color: #64748b !important; }
    .stMainBlockContainer .stMarkdown p,
    .stMainBlockContainer .stMarkdown li,
    .stMainBlockContainer .stMarkdown span { color: #cbd5e1; }
    .stMainBlockContainer .stMarkdown h1,
    .stMainBlockContainer .stMarkdown h2,
    .stMainBlockContainer .stMarkdown h3,
    .stMainBlockContainer .stMarkdown h4,
    .stMainBlockContainer .stMarkdown h5 { color: #e2e8f0; }
    .stMainBlockContainer .stMarkdown hr { border-color: rgba(51,65,85,0.5); }
    .stMainBlockContainer .stMarkdown code {
        background: rgba(30,41,59,0.8); color: #60a5fa;
        padding: 0.15rem 0.4rem; border-radius: 0.25rem; font-size: 0.85em;
    }

    /* Download button */
    [data-testid="stDownloadButton"] button {
        background: rgba(30,41,59,0.8) !important;
        color: #60a5fa !important;
        border: 1px solid rgba(59,130,246,0.3) !important;
        border-radius: 0.5rem !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: rgba(59,130,246,0.1) !important;
        border-color: #3b82f6 !important;
    }

    /* Checkbox */
    [data-testid="stCheckbox"] label span { color: #94a3b8 !important; }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY COMPONENTS (inline CSS — no Tailwind CDN needed)
# ═══════════════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = "", icon: str = "📊",
                gradient: str = "linear-gradient(135deg,rgba(37,99,235,0.9),rgba(79,70,229,0.85))") -> str:
    """Gradient page header card."""
    sub_html = f'<p style="margin:0.3rem 0 0 0;font-size:0.9rem;color:rgba(219,234,254,0.7);">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="background:{gradient};
                border-radius:0.75rem;padding:1.5rem 2rem;margin-bottom:1.5rem;
                border:1px solid rgba(96,165,250,0.2);
                box-shadow:0 10px 25px -5px rgba(0,0,0,0.3);">
        <h1 style="margin:0;font-size:1.8rem;font-weight:700;color:white;
                   font-family:'Inter',sans-serif;display:flex;align-items:center;gap:0.5rem;">
            <span>{icon}</span> {title}
        </h1>
        {sub_html}
    </div>
    """


def section_title(text: str, icon: str = "📋") -> str:
    """Section heading with accent bar."""
    return f"""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1.5rem 0 1rem 0;">
        <div style="width:3px;height:1.5rem;background:#3b82f6;border-radius:2px;"></div>
        <h3 style="margin:0;font-size:1.1rem;font-weight:600;color:#e2e8f0;
                   font-family:'Inter',sans-serif;">{icon} {text}</h3>
    </div>
    """


def metric_card(label: str, value: str, icon: str = "📊",
                color: str = "blue") -> str:
    """Single metric card. Returns HTML string."""
    colors = {
        "blue":   {"grad": "rgba(59,130,246,0.12),rgba(37,99,235,0.05)",  "border": "rgba(59,130,246,0.25)",  "text": "#60a5fa"},
        "green":  {"grad": "rgba(16,185,129,0.12),rgba(5,150,105,0.05)",  "border": "rgba(16,185,129,0.25)",  "text": "#34d399"},
        "orange": {"grad": "rgba(249,115,22,0.12),rgba(234,88,12,0.05)",  "border": "rgba(249,115,22,0.25)",  "text": "#fb923c"},
        "purple": {"grad": "rgba(139,92,246,0.12),rgba(124,58,237,0.05)", "border": "rgba(139,92,246,0.25)",  "text": "#a78bfa"},
        "cyan":   {"grad": "rgba(6,182,212,0.12),rgba(8,145,178,0.05)",   "border": "rgba(6,182,212,0.25)",   "text": "#22d3ee"},
        "red":    {"grad": "rgba(239,68,68,0.12),rgba(220,38,38,0.05)",   "border": "rgba(239,68,68,0.25)",   "text": "#f87171"},
    }
    c = colors.get(color, colors["blue"])

    return f"""
    <div style="background:linear-gradient(135deg,{c['grad']});
                border:1px solid {c['border']};border-radius:0.75rem;
                padding:1.25rem;transition:all 0.2s ease;">
        <p style="margin:0 0 0.5rem 0;font-size:0.7rem;font-weight:600;
                  color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;
                  font-family:'Inter',sans-serif;">
            {icon} {label}
        </p>
        <p style="margin:0;font-size:1.5rem;font-weight:700;color:{c['text']};
                  font-family:'Inter',sans-serif;">{value}</p>
    </div>
    """


def metric_row(cards: List[str]) -> str:
    """Responsive grid of metric cards (uses CSS grid)."""
    n = len(cards)
    inner = "".join(cards)
    return f"""
    <div style="display:grid;grid-template-columns:repeat({n},1fr);gap:1rem;margin-bottom:1.5rem;">
        {inner}
    </div>
    """


def info_banner(text: str, type: str = "info") -> str:
    """Info/warning/success/error banner."""
    styles = {
        "info":    {"bg": "rgba(59,130,246,0.08)",  "border": "rgba(59,130,246,0.25)",  "text": "#60a5fa",  "emoji": "ℹ️"},
        "success": {"bg": "rgba(16,185,129,0.08)",  "border": "rgba(16,185,129,0.25)",  "text": "#34d399",  "emoji": "✅"},
        "warning": {"bg": "rgba(245,158,11,0.08)",  "border": "rgba(245,158,11,0.25)",  "text": "#fbbf24",  "emoji": "⚠️"},
        "error":   {"bg": "rgba(239,68,68,0.08)",   "border": "rgba(239,68,68,0.25)",   "text": "#f87171",  "emoji": "❌"},
    }
    s = styles.get(type, styles["info"])
    return f"""
    <div style="background:{s['bg']};border:1px solid {s['border']};
                border-radius:0.5rem;padding:0.75rem 1rem;margin-bottom:1rem;">
        <p style="margin:0;color:{s['text']};font-size:0.875rem;font-weight:500;
                  font-family:'Inter',sans-serif;">{s['emoji']} {text}</p>
    </div>
    """


def data_table(headers: List[str], rows: List[List[str]],
               col_aligns: Optional[List[str]] = None,
               highlight_last_row: bool = False,
               compact: bool = False) -> str:
    """
    Styled data table with inline CSS.

    Args:
        headers: Column header labels
        rows: List of row data (list of strings, already formatted)
        col_aligns: 'l', 'c', or 'r' per column (default: first col centered, rest right)
        highlight_last_row: Style last row as total
        compact: Use smaller padding
    """
    n_cols = len(headers)
    if col_aligns is None:
        col_aligns = ["c"] + ["r"] * (n_cols - 1)

    align_map = {"l": "left", "c": "center", "r": "right"}
    pad = "6px 10px" if compact else "10px 14px"

    # Header
    header_cells = "".join(
        f'<th style="padding:{pad};text-align:{align_map.get(col_aligns[i], "right")};'
        f'font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;'
        f'color:#cbd5e1;background:rgba(30,41,59,0.9);border-bottom:1px solid rgba(51,65,85,0.5);">'
        f'{h}</th>'
        for i, h in enumerate(headers)
    )

    # Body rows
    body_html = ""
    for ri, row in enumerate(rows):
        is_total = highlight_last_row and ri == len(rows) - 1
        if is_total:
            bg = "rgba(51,65,85,0.8)"
            text_color = "#ffffff"
            font_weight = "700"
        else:
            bg = "rgba(30,41,59,0.3)" if ri % 2 == 0 else "rgba(30,41,59,0.1)"
            text_color = "#cbd5e1"
            font_weight = "400"

        cells = ""
        for ci, cell in enumerate(row):
            align = align_map.get(col_aligns[ci] if ci < len(col_aligns) else "r", "right")
            extra_w = "font-weight:600;color:#e2e8f0;" if ci == 0 else ""
            extra_w += f"font-weight:{font_weight};" if is_total else ""
            cells += (
                f'<td style="padding:{pad};text-align:{align};color:{text_color};'
                f'font-size:0.875rem;border-bottom:1px solid rgba(51,65,85,0.2);{extra_w}">'
                f'{cell}</td>'
            )
        body_html += f'<tr style="background:{bg};">{cells}</tr>'

    return f"""
    <div style="border-radius:0.75rem;border:1px solid rgba(51,65,85,0.5);
                overflow:hidden;margin-bottom:1.5rem;
                box-shadow:0 10px 15px -3px rgba(0,0,0,0.2);">
        <table style="width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{body_html}</tbody>
        </table>
    </div>
    """


def card_list_item(left_content: str, right_content: str = "",
                   tag: str = "", tag_color: str = "blue") -> str:
    """Single card-list row item."""
    colors = {
        "blue":   {"bg": "rgba(59,130,246,0.15)",  "text": "#60a5fa"},
        "green":  {"bg": "rgba(16,185,129,0.15)",  "text": "#34d399"},
        "orange": {"bg": "rgba(249,115,22,0.15)",  "text": "#fb923c"},
        "red":    {"bg": "rgba(239,68,68,0.15)",   "text": "#f87171"},
        "purple": {"bg": "rgba(139,92,246,0.15)",  "text": "#a78bfa"},
    }
    c = colors.get(tag_color, colors["blue"])

    tag_html = (
        f'<span style="padding:0.15rem 0.5rem;background:{c["bg"]};color:{c["text"]};'
        f'border-radius:0.25rem;font-size:0.75rem;font-weight:600;'
        f'font-family:\'Inter\',sans-serif;">{tag}</span>'
    ) if tag else ""

    right_html = (
        f'<span style="font-size:0.875rem;color:#64748b;font-family:\'Inter\',sans-serif;">'
        f'{right_content}</span>'
    ) if right_content else ""

    return f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:0.875rem 1rem;background:rgba(30,41,59,0.4);
                border-radius:0.5rem;border:1px solid rgba(51,65,85,0.4);
                margin-bottom:0.5rem;">
        <div style="display:flex;align-items:center;gap:0.75rem;">
            {tag_html}
            <span style="font-size:0.875rem;color:#cbd5e1;font-family:'Inter',sans-serif;">
                {left_content}
            </span>
        </div>
        {right_html}
    </div>
    """


def divider() -> str:
    """Subtle horizontal divider."""
    return '<hr style="margin:1.5rem 0;border:none;border-top:1px solid rgba(51,65,85,0.5);">'


# ═══════════════════════════════════════════════════════════════════════════════
# PAGINATED DATAFRAME
# ═══════════════════════════════════════════════════════════════════════════════

def paginated_dataframe(
    df,
    key_prefix: str,
    page_sizes: Optional[List[int]] = None,
    default_page_size: int = 20,
    height: Optional[int] = None,
):
    """
    Render a paginated st.dataframe with page-size selector and navigation.

    Args:
        df: pandas DataFrame to display
        key_prefix: unique prefix for session state keys (allows multiple instances)
        page_sizes: list of page size options
        default_page_size: default rows per page
        height: optional fixed height for the dataframe widget
    """
    import streamlit as st
    import math

    if df is None or df.empty:
        st.markdown(info_banner("Không có dữ liệu để hiển thị.", "info"), unsafe_allow_html=True)
        return

    if page_sizes is None:
        page_sizes = [10, 20, 30, 40, 50, 100]

    total_rows = len(df)

    # Session state keys
    ps_key = f"{key_prefix}_page_size"
    pg_key = f"{key_prefix}_page"

    # Initialize session state
    if ps_key not in st.session_state:
        st.session_state[ps_key] = default_page_size
    if pg_key not in st.session_state:
        st.session_state[pg_key] = 0

    page_size = st.session_state[ps_key]
    total_pages = max(1, math.ceil(total_rows / page_size))

    # Clamp current page
    if st.session_state[pg_key] >= total_pages:
        st.session_state[pg_key] = total_pages - 1
    if st.session_state[pg_key] < 0:
        st.session_state[pg_key] = 0

    current_page = st.session_state[pg_key]

    # ── Navigation bar ──
    nav_cols = st.columns([1.2, 0.6, 0.6, 0.6, 2])

    with nav_cols[0]:
        new_size = st.selectbox(
            "Số dòng/trang",
            page_sizes,
            index=page_sizes.index(page_size) if page_size in page_sizes else 0,
            key=f"{key_prefix}_ps_select",
            label_visibility="collapsed",
        )
        if new_size != page_size:
            st.session_state[ps_key] = new_size
            st.session_state[pg_key] = 0
            st.rerun()

    with nav_cols[1]:
        if st.button("◀", key=f"{key_prefix}_prev", disabled=(current_page == 0)):
            st.session_state[pg_key] = current_page - 1
            st.rerun()

    with nav_cols[2]:
        st.markdown(
            f"<div style='text-align:center;padding:0.4rem 0;color:#94a3b8;font-size:0.85rem;'>"
            f"Trang <strong style='color:#e2e8f0;'>{current_page + 1}</strong> / {total_pages}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with nav_cols[3]:
        if st.button("▶", key=f"{key_prefix}_next", disabled=(current_page >= total_pages - 1)):
            st.session_state[pg_key] = current_page + 1
            st.rerun()

    with nav_cols[4]:
        start_row = current_page * page_size + 1
        end_row = min((current_page + 1) * page_size, total_rows)
        st.markdown(
            f"<div style='text-align:right;padding:0.4rem 0;color:#64748b;font-size:0.8rem;'>"
            f"Hiển thị {start_row:,}–{end_row:,} / {total_rows:,} dòng"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Data slice ──
    start_idx = current_page * page_size
    end_idx = start_idx + page_size
    page_df = df.iloc[start_idx:end_idx]

    kwargs = dict(use_container_width=True, hide_index=True)
    if height is not None:
        kwargs["height"] = height

    st.dataframe(page_df, **kwargs)
