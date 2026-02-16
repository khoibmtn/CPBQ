"""
tw_components.py – Streamlit component library (inline CSS, no Tailwind CDN)
=============================================================================
Reusable HTML helpers that render via st.markdown(unsafe_allow_html=True).
Uses CSS custom properties for light/dark theme support.
All functions return HTML strings — no Streamlit widget calls inside.
"""

import streamlit as st
from typing import List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# THEME HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_theme() -> str:
    """Return current theme: 'dark' or 'light'."""
    return st.session_state.get("theme", "dark")


def inject_theme_css():
    """Inject CSS custom properties for both themes. Called once at app startup."""
    st.markdown("""
    <style>
    /* ── Dark theme (default) ── */
    :root, [data-theme="dark"] {
        --bg-app-from: #0f172a;
        --bg-app-to: #1e293b;
        --bg-sidebar-from: #1e293b;
        --bg-sidebar-to: #0f172a;
        --bg-card: rgba(30,41,59,0.8);
        --bg-card-alt: rgba(30,41,59,0.4);
        --bg-card-subtle: rgba(30,41,59,0.5);
        --bg-card-border: rgba(51,65,85,0.5);
        --bg-input: rgba(30,41,59,0.8);
        --bg-input-border: rgba(51,65,85,0.8);
        --bg-hover: rgba(51,65,85,0.6);
        --bg-hover-accent: rgba(59,130,246,0.08);
        --bg-active-accent: rgba(59,130,246,0.15);
        --bg-table-header: rgba(30,41,59,0.9);
        --bg-table-row-even: rgba(30,41,59,0.3);
        --bg-table-row-odd: rgba(30,41,59,0.1);
        --bg-table-total: rgba(51,65,85,0.8);
        --bg-code: rgba(30,41,59,0.8);

        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --text-body: #cbd5e1;
        --text-heading: #e2e8f0;
        --text-table: #cbd5e1;
        --text-table-header: #cbd5e1;
        --text-total: #ffffff;
        --text-on-card: #94a3b8;

        --accent: #3b82f6;
        --accent-light: #60a5fa;
        --accent-hover: rgba(59,130,246,0.2);
        --accent-shadow: rgba(59,130,246,0.3);

        --border: rgba(51,65,85,0.5);
        --border-muted: rgba(51,65,85,0.2);
        --border-accent: rgba(59,130,246,0.3);
        --sidebar-border: rgba(51,65,85,0.5);

        --shadow-card: 0 10px 25px -5px rgba(0,0,0,0.3);
        --shadow-table: 0 10px 15px -3px rgba(0,0,0,0.2);
        --shadow-btn: 0 2px 8px rgba(59,130,246,0.3);
        --shadow-btn-hover: 0 4px 16px rgba(59,130,246,0.4);

        /* Table-specific */
        --tbl-border: #475569;
        --tbl-th-bg: #1e293b;
        --tbl-th-color: #f8fafc;
        --tbl-td-color: #f1f5f9;
        --tbl-col-fixed-bg: #334155;
        --tbl-col-fixed-color: #f8fafc;
        --tbl-col-fixed-muted: #cbd5e1;
        --tbl-row-even: #1e293b;
        --tbl-row-odd: #263548;
        --tbl-row-total: #172033;
        --tbl-row-subtotal: #1a2744;
        --tbl-section-bg: #0f172a;
        --tbl-section-color: #60a5fa;
        --tbl-subtotal-color: #93c5fd;
        --tbl-sub-header-bg: #334155;
        --tbl-diff-pos: #86efac;
        --tbl-diff-neg: #fca5a5;

        /* Sidebar text */
        --sidebar-text: #94a3b8;
        --sidebar-text-hover: #e2e8f0;
        --sidebar-active-text: #60a5fa;
        --sidebar-caption: rgba(148,163,184,0.5);
    }

    /* ── Light theme ── */
    [data-theme="light"] {
        --bg-app-from: #f1f5f9;
        --bg-app-to: #e2e8f0;
        --bg-sidebar-from: #ffffff;
        --bg-sidebar-to: #f8fafc;
        --bg-card: #ffffff;
        --bg-card-alt: #f8fafc;
        --bg-card-subtle: #f1f5f9;
        --bg-card-border: rgba(203,213,225,0.8);
        --bg-input: #ffffff;
        --bg-input-border: rgba(203,213,225,0.8);
        --bg-hover: rgba(241,245,249,0.8);
        --bg-hover-accent: rgba(59,130,246,0.06);
        --bg-active-accent: rgba(59,130,246,0.1);
        --bg-table-header: #f1f5f9;
        --bg-table-row-even: #ffffff;
        --bg-table-row-odd: #f8fafc;
        --bg-table-total: #e2e8f0;
        --bg-code: #f1f5f9;

        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --text-body: #334155;
        --text-heading: #0f172a;
        --text-table: #334155;
        --text-table-header: #475569;
        --text-total: #0f172a;
        --text-on-card: #64748b;

        --accent: #2563eb;
        --accent-light: #3b82f6;
        --accent-hover: rgba(37,99,235,0.15);
        --accent-shadow: rgba(37,99,235,0.2);

        --border: rgba(203,213,225,0.8);
        --border-muted: rgba(226,232,240,0.6);
        --border-accent: rgba(59,130,246,0.3);
        --sidebar-border: rgba(226,232,240,0.8);

        --shadow-card: 0 4px 12px -2px rgba(0,0,0,0.08);
        --shadow-table: 0 4px 8px -2px rgba(0,0,0,0.06);
        --shadow-btn: 0 2px 6px rgba(37,99,235,0.2);
        --shadow-btn-hover: 0 4px 12px rgba(37,99,235,0.3);

        /* Table-specific */
        --tbl-border: #cbd5e1;
        --tbl-th-bg: #f1f5f9;
        --tbl-th-color: #1e293b;
        --tbl-td-color: #334155;
        --tbl-col-fixed-bg: #e2e8f0;
        --tbl-col-fixed-color: #1e293b;
        --tbl-col-fixed-muted: #475569;
        --tbl-row-even: #ffffff;
        --tbl-row-odd: #f8fafc;
        --tbl-row-total: #e2e8f0;
        --tbl-row-subtotal: #eff6ff;
        --tbl-section-bg: #f8fafc;
        --tbl-section-color: #2563eb;
        --tbl-subtotal-color: #1d4ed8;
        --tbl-sub-header-bg: #e2e8f0;
        --tbl-diff-pos: #16a34a;
        --tbl-diff-neg: #dc2626;

        /* Sidebar text */
        --sidebar-text: #475569;
        --sidebar-text-hover: #1e293b;
        --sidebar-active-text: #2563eb;
        --sidebar-caption: rgba(100,116,139,0.6);
    }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: CSS INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_tailwind():
    """Inject Google Fonts. Called once at app startup."""
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)


def override_streamlit_widgets():
    """CSS overrides to restyle Streamlit widgets using theme variables."""
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
        background: linear-gradient(135deg, var(--bg-app-from) 0%, var(--bg-app-to) 50%, var(--bg-app-from) 100%);
    }
    .stMainBlockContainer {
        max-width: 1200px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-sidebar-from) 0%, var(--bg-sidebar-to) 100%);
        border-right: 1px solid var(--sidebar-border);
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
        border-color: var(--sidebar-border);
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] label {
        color: var(--sidebar-text) !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: var(--sidebar-caption) !important;
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
        content: '✕'; font-size: 1.1rem; color: var(--sidebar-text);
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
        content: '☰'; font-size: 1.3rem; color: var(--sidebar-text);
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
        background: transparent !important; color: var(--sidebar-text) !important;
        font-weight: 500; box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: var(--bg-hover-accent) !important;
        color: var(--sidebar-text-hover) !important;
        box-shadow: -11px 0 0 0 var(--bg-hover-accent), 11px 0 0 0 var(--bg-hover-accent) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--bg-active-accent) !important;
        color: var(--sidebar-active-text) !important; font-weight: 600;
        border-left: 3px solid var(--accent) !important;
        box-shadow: -11px 0 0 0 var(--bg-active-accent), 11px 0 0 0 var(--bg-active-accent) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
        box-shadow: -11px 0 0 0 var(--accent-hover), 11px 0 0 0 var(--accent-hover) !important;
    }
    [data-testid="stSidebar"] .stButton > button:focus {
        outline: none !important;
    }

    /* ── Restyle Streamlit native widgets ── */

    /* Selectbox */
    [data-testid="stSelectbox"] label {
        color: var(--text-secondary) !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stSelectbox"] > div > div {
        background: var(--bg-input) !important;
        border: 1px solid var(--bg-input-border) !important;
        border-radius: 0.5rem !important; color: var(--text-primary) !important;
    }

    /* Text input */
    [data-testid="stTextInput"] label {
        color: var(--text-secondary) !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stTextInput"] input {
        background: var(--bg-input) !important;
        border: 1px solid var(--bg-input-border) !important;
        border-radius: 0.5rem !important; color: var(--text-primary) !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px var(--accent-shadow) !important;
    }

    /* Multiselect */
    [data-testid="stMultiSelect"] label {
        color: var(--text-secondary) !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stMultiSelect"] > div > div {
        background: var(--bg-input) !important;
        border: 1px solid var(--bg-input-border) !important;
        border-radius: 0.5rem !important;
    }

    /* Buttons (main area) */
    .stMainBlockContainer .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent)) !important;
        color: white !important; border: none !important;
        border-radius: 0.5rem !important; font-weight: 600;
        padding: 0.5rem 1.25rem; transition: all 0.2s ease;
        box-shadow: var(--shadow-btn) !important;
    }
    .stMainBlockContainer .stButton > button[kind="primary"]:hover {
        box-shadow: var(--shadow-btn-hover) !important;
        transform: translateY(-1px);
    }
    .stMainBlockContainer .stButton > button[kind="secondary"] {
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--bg-card-border) !important;
        border-radius: 0.5rem !important; font-weight: 500;
        transition: all 0.2s ease;
    }
    .stMainBlockContainer .stButton > button[kind="secondary"]:hover {
        background: var(--bg-hover) !important;
        color: var(--text-primary) !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] label {
        color: var(--text-secondary) !important; font-size: 0.85rem; font-weight: 500;
    }
    [data-testid="stFileUploader"] section {
        background: var(--bg-card-subtle) !important;
        border: 2px dashed var(--bg-card-border) !important;
        border-radius: 0.75rem !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--border-accent) !important;
        background: var(--bg-hover-accent) !important;
    }

    /* Radio buttons */
    [data-testid="stRadio"] label { color: var(--text-secondary) !important; }
    [data-testid="stRadio"] p { color: var(--text-body) !important; }

    /* Tabs */
    [data-testid="stTabs"] button[data-baseweb="tab"] {
        color: var(--text-muted) !important; font-weight: 500;
        border-bottom: 2px solid transparent !important;
        transition: all 0.2s ease;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent-light) !important;
        border-bottom: 2px solid var(--accent) !important;
        font-weight: 600;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"]:hover {
        color: var(--accent-light) !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: var(--bg-card-subtle) !important;
        border: 1px solid var(--bg-card-border) !important;
        border-radius: 0.75rem !important;
    }
    [data-testid="stExpander"] summary span {
        color: var(--text-secondary) !important; font-weight: 500;
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
    .stSpinner > div { color: var(--accent-light) !important; }

    /* Alert boxes */
    [data-testid="stAlert"] {
        background: var(--bg-card-subtle) !important;
        border: 1px solid var(--bg-card-border) !important;
        border-radius: 0.75rem !important;
        color: var(--text-body) !important;
    }

    /* Progress bar */
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, var(--accent), #0ea5e9) !important;
        border-radius: 0.25rem;
    }

    /* Caption & text */
    .stCaption { color: var(--text-muted) !important; }
    .stMainBlockContainer .stMarkdown p,
    .stMainBlockContainer .stMarkdown li,
    .stMainBlockContainer .stMarkdown span { color: var(--text-body); }
    .stMainBlockContainer .stMarkdown h1,
    .stMainBlockContainer .stMarkdown h2,
    .stMainBlockContainer .stMarkdown h3,
    .stMainBlockContainer .stMarkdown h4,
    .stMainBlockContainer .stMarkdown h5 { color: var(--text-heading); }
    .stMainBlockContainer .stMarkdown hr { border-color: var(--border); }
    .stMainBlockContainer .stMarkdown code {
        background: var(--bg-code); color: var(--accent-light);
        padding: 0.15rem 0.4rem; border-radius: 0.25rem; font-size: 0.85em;
    }

    /* Download button */
    [data-testid="stDownloadButton"] button {
        background: var(--bg-card) !important;
        color: var(--accent-light) !important;
        border: 1px solid var(--border-accent) !important;
        border-radius: 0.5rem !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: var(--bg-hover-accent) !important;
        border-color: var(--accent) !important;
    }

    /* Checkbox */
    [data-testid="stCheckbox"] label span { color: var(--text-secondary) !important; }

    /* Popover */
    [data-testid="stPopover"] > div > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--bg-card-border) !important;
    }
    </style>
    """, unsafe_allow_html=True)


def inject_theme_script():
    """Inject a script to set data-theme attribute on <html>."""
    theme = get_theme()
    st.markdown(f"""
    <script>
        document.documentElement.setAttribute('data-theme', '{theme}');
    </script>
    """, unsafe_allow_html=True)

    # Fallback: also set via CSS if script is stripped
    if theme == "light":
        st.markdown("""
        <style>
        :root {
            --bg-app-from: #f1f5f9;
            --bg-app-to: #e2e8f0;
            --bg-sidebar-from: #ffffff;
            --bg-sidebar-to: #f8fafc;
            --bg-card: #ffffff;
            --bg-card-alt: #f8fafc;
            --bg-card-subtle: #f1f5f9;
            --bg-card-border: rgba(203,213,225,0.8);
            --bg-input: #ffffff;
            --bg-input-border: rgba(203,213,225,0.8);
            --bg-hover: rgba(241,245,249,0.8);
            --bg-hover-accent: rgba(59,130,246,0.06);
            --bg-active-accent: rgba(59,130,246,0.1);
            --bg-table-header: #f1f5f9;
            --bg-table-row-even: #ffffff;
            --bg-table-row-odd: #f8fafc;
            --bg-table-total: #e2e8f0;
            --bg-code: #f1f5f9;

            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --text-body: #334155;
            --text-heading: #0f172a;
            --text-table: #334155;
            --text-table-header: #475569;
            --text-total: #0f172a;
            --text-on-card: #64748b;

            --accent: #2563eb;
            --accent-light: #3b82f6;
            --accent-hover: rgba(37,99,235,0.15);
            --accent-shadow: rgba(37,99,235,0.2);

            --border: rgba(203,213,225,0.8);
            --border-muted: rgba(226,232,240,0.6);
            --border-accent: rgba(59,130,246,0.3);
            --sidebar-border: rgba(226,232,240,0.8);

            --shadow-card: 0 4px 12px -2px rgba(0,0,0,0.08);
            --shadow-table: 0 4px 8px -2px rgba(0,0,0,0.06);
            --shadow-btn: 0 2px 6px rgba(37,99,235,0.2);
            --shadow-btn-hover: 0 4px 12px rgba(37,99,235,0.3);

            --tbl-border: #cbd5e1;
            --tbl-th-bg: #f1f5f9;
            --tbl-th-color: #1e293b;
            --tbl-td-color: #334155;
            --tbl-col-fixed-bg: #e2e8f0;
            --tbl-col-fixed-color: #1e293b;
            --tbl-col-fixed-muted: #475569;
            --tbl-row-even: #ffffff;
            --tbl-row-odd: #f8fafc;
            --tbl-row-total: #e2e8f0;
            --tbl-row-subtotal: #eff6ff;
            --tbl-section-bg: #f8fafc;
            --tbl-section-color: #2563eb;
            --tbl-subtotal-color: #1d4ed8;
            --tbl-sub-header-bg: #e2e8f0;
            --tbl-diff-pos: #16a34a;
            --tbl-diff-neg: #dc2626;

            --sidebar-text: #475569;
            --sidebar-text-hover: #1e293b;
            --sidebar-active-text: #2563eb;
            --sidebar-caption: rgba(100,116,139,0.6);
        }
        </style>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY COMPONENTS (inline CSS — using CSS variables)
# ═══════════════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = "", icon: str = "📊",
                gradient: str = "linear-gradient(135deg,rgba(37,99,235,0.9),rgba(79,70,229,0.85))") -> str:
    """Gradient page header card."""
    sub_html = f'<p style="margin:0.3rem 0 0 0;font-size:0.9rem;color:rgba(219,234,254,0.7);">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="background:{gradient};
                border-radius:0.75rem;padding:1.5rem 2rem;margin-bottom:1.5rem;
                border:1px solid rgba(96,165,250,0.2);
                box-shadow:var(--shadow-card);">
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
        <div style="width:3px;height:1.5rem;background:var(--accent);border-radius:2px;"></div>
        <h3 style="margin:0;font-size:1.1rem;font-weight:600;color:var(--text-heading);
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
                  color:var(--text-on-card);text-transform:uppercase;letter-spacing:0.05em;
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
    """Styled data table with CSS variable theming."""
    n_cols = len(headers)
    if col_aligns is None:
        col_aligns = ["c"] + ["r"] * (n_cols - 1)

    align_map = {"l": "left", "c": "center", "r": "right"}
    pad = "6px 10px" if compact else "10px 14px"

    # Header
    header_cells = "".join(
        f'<th style="padding:{pad};text-align:{align_map.get(col_aligns[i], "right")};'
        f'font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;'
        f'color:var(--text-table-header);background:var(--bg-table-header);border-bottom:1px solid var(--border);">'
        f'{h}</th>'
        for i, h in enumerate(headers)
    )

    # Body rows
    body_html = ""
    for ri, row in enumerate(rows):
        is_total = highlight_last_row and ri == len(rows) - 1
        if is_total:
            bg = "var(--bg-table-total)"
            text_color = "var(--text-total)"
            font_weight = "700"
        else:
            bg = "var(--bg-table-row-even)" if ri % 2 == 0 else "var(--bg-table-row-odd)"
            text_color = "var(--text-table)"
            font_weight = "400"

        cells = ""
        for ci, cell in enumerate(row):
            align = align_map.get(col_aligns[ci] if ci < len(col_aligns) else "r", "right")
            extra_w = f"font-weight:600;color:var(--text-primary);" if ci == 0 else ""
            extra_w += f"font-weight:{font_weight};" if is_total else ""
            cells += (
                f'<td style="padding:{pad};text-align:{align};color:{text_color};'
                f'font-size:0.875rem;border-bottom:1px solid var(--border-muted);{extra_w}">'
                f'{cell}</td>'
            )
        body_html += f'<tr style="background:{bg};">{cells}</tr>'

    return f"""
    <div style="border-radius:0.75rem;border:1px solid var(--border);
                overflow:hidden;margin-bottom:1.5rem;
                box-shadow:var(--shadow-table);">
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
        f"font-family:'Inter',sans-serif;\">{tag}</span>"
    ) if tag else ""

    right_html = (
        f'<span style="font-size:0.875rem;color:var(--text-muted);font-family:\'Inter\',sans-serif;">'
        f'{right_content}</span>'
    ) if right_content else ""

    return f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:0.875rem 1rem;background:var(--bg-card-alt);
                border-radius:0.5rem;border:1px solid var(--bg-card-border);
                margin-bottom:0.5rem;">
        <div style="display:flex;align-items:center;gap:0.75rem;">
            {tag_html}
            <span style="font-size:0.875rem;color:var(--text-body);font-family:'Inter',sans-serif;">
                {left_content}
            </span>
        </div>
        {right_html}
    </div>
    """


def divider() -> str:
    """Subtle horizontal divider."""
    return '<hr style="margin:1.5rem 0;border:none;border-top:1px solid var(--border);">'


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
            f"<div style='text-align:center;padding:0.4rem 0;color:var(--text-secondary);font-size:0.85rem;'>"
            f"Trang <strong style='color:var(--text-primary);'>{current_page + 1}</strong> / {total_pages}"
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
            f"<div style='text-align:right;padding:0.4rem 0;color:var(--text-muted);font-size:0.8rem;'>"
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
