#!/usr/bin/env python3
# v2026.02.12 – comparison table update
"""
app.py - CPBQ Dashboard
========================
Sử dụng: source venv/bin/activate && streamlit run app.py

Giao diện quản lý dữ liệu thanh toán BHYT:
  - Tổng quan: Bảng tổng hợp theo tháng / nội-ngoại trú / CSKCB
  - Cài đặt: Quản lý bảng mã lookup
"""

import streamlit as st

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CPBQ Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State ────────────────────────────────────────────────────────────

if "current_page" not in st.session_state:
    st.session_state.current_page = "overview"

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3a5c 0%, #3b4874 100%);
    }
    /* Remove sidebar inner padding so buttons reach edges */
    [data-testid="stSidebar"] > div:first-child {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    /* Re-add padding for non-button content */
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stHorizontalBlock {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    [data-testid="stSidebar"] hr {
        margin-left: 1rem;
        margin-right: 1rem;
    }

    /* ── Sidebar collapse / expand buttons ── */
    /* Hide text in both close and open sidebar buttons, replace with icons */
    button[data-testid="stBaseButton-headerNoPadding"] {
        overflow: hidden;
        position: relative;
        width: 2.2rem;
        height: 2.2rem;
        min-height: unset;
        padding: 0 !important;
    }
    button[data-testid="stBaseButton-headerNoPadding"] span {
        font-size: 0 !important;
        visibility: hidden;
    }
    button[data-testid="stBaseButton-headerNoPadding"]::after {
        visibility: visible;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    /* Close button (inside sidebar) → ✕ */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"] {
        margin-left: 0.5rem;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"]::after {
        content: '✕';
        font-size: 1.1rem;
        color: #cbd5e1;
    }
    /* Open/expand button (outside sidebar when collapsed) → ☰ */
    button[data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"] button {
        overflow: hidden !important;
        position: relative;
        width: 2.2rem;
        height: 2.2rem;
        min-height: unset;
        padding: 0 !important;
    }
    button[data-testid="stExpandSidebarButton"] span,
    [data-testid="stSidebarCollapsedControl"] button span {
        font-size: 0 !important;
        visibility: hidden;
    }
    button[data-testid="stExpandSidebarButton"]::after,
    [data-testid="stSidebarCollapsedControl"] button::after {
        content: '☰';
        font-size: 1.3rem;
        color: #cbd5e1;
        visibility: visible;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }

    /* ── Sidebar menu buttons (edge-to-edge) ── */
    [data-testid="stSidebar"] .stElementContainer:has(.stButton) {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    [data-testid="stSidebar"] .stButton {
        margin-left: 0;
        margin-right: 0;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        text-align: left;
        padding: 0.75rem 1.2rem;
        border-radius: 0;
        border: none !important;
        font-size: 0.95rem;
        font-family: 'Inter', sans-serif;
        cursor: pointer;
        transition: all 0.15s ease;
        margin-bottom: 0;
    }

    /* Inactive (secondary) */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #cbd5e1 !important;
        font-weight: 500;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.08) !important;
        color: #ffffff !important;
        box-shadow: -11px 0 0 0 rgba(255,255,255,0.08), 11px 0 0 0 rgba(255,255,255,0.08) !important;
    }

    /* Active (primary) – box-shadow spreads color to sidebar edges */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: rgba(99,130,202,0.45) !important;
        color: #ffffff !important;
        font-weight: 600;
        box-shadow: -11px 0 0 0 rgba(99,130,202,0.45), 11px 0 0 0 rgba(99,130,202,0.45) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: rgba(99,130,202,0.55) !important;
        box-shadow: -11px 0 0 0 rgba(99,130,202,0.55), 11px 0 0 0 rgba(99,130,202,0.55) !important;
    }

    /* Remove focus ring (keep box-shadow for edge highlight) */
    [data-testid="stSidebar"] .stButton > button:focus {
        outline: none !important;
    }

    /* Caption in sidebar */
    [data-testid="stSidebar"] .stCaption {
        color: rgba(203,213,225,0.5) !important;
    }

    /* ── Header gradient ── */
    .main-header {
        background: linear-gradient(135deg, #0ea5e9, #2563eb);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }

    /* ── Table styling ── */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    .stDataFrame thead th {
        background-color: #1e293b !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* ── Metric cards — both themes ── */
    [data-testid="stMetric"] {
        background: rgba(14, 165, 233, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #0ea5e9;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar Navigation (Page Menu) ──────────────────────────────────────────

PAGES = [
    {"key": "overview",        "label": "📊  Tổng quan",       "icon": "📊"},
    {"key": "cost_by_dept",    "label": "🏥  CP theo khoa",    "icon": "🏥"},
    {"key": "hospital_stats",  "label": "🏛️  Toàn viện",       "icon": "🏛️"},
    {"key": "icd_analysis",    "label": "🔬  Phân tích ICD",   "icon": "🔬"},
    {"key": "settings",        "label": "⚙️  Cài đặt",        "icon": "⚙️"},
]

st.sidebar.markdown("### 🏥 CPBQ Dashboard")
st.sidebar.markdown("---")

for p in PAGES:
    is_active = st.session_state.current_page == p["key"]
    btn_type = "primary" if is_active else "secondary"
    if st.sidebar.button(
        p["label"],
        key=f"nav_{p['key']}",
        use_container_width=True,
        type=btn_type,
    ):
        st.session_state.current_page = p["key"]
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("TTYT Thủy Nguyên · v1.0")

# ─── Page Routing ─────────────────────────────────────────────────────────────

if st.session_state.current_page == "overview":
    from views.overview import render
    render()
elif st.session_state.current_page == "cost_by_dept":
    from views.cost_by_dept import render
    render()
elif st.session_state.current_page == "hospital_stats":
    from views.hospital_stats import render
    render()
elif st.session_state.current_page == "icd_analysis":
    from views.icd_analysis import render
    render()
elif st.session_state.current_page == "settings":
    from views.settings import render
    render()
