#!/usr/bin/env python3
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

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }

    /* Header gradient */
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

    /* Table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    .stDataFrame thead th {
        background-color: #1e293b !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* Metric cards — works in both light and dark themes */
    [data-testid="stMetric"] {
        background: rgba(14, 165, 233, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #0ea5e9;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar Navigation ──────────────────────────────────────────────────────

st.sidebar.markdown("## 🏥 CPBQ Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "📌 Chọn trang",
    ["📊 Tổng quan", "⚙️ Cài đặt"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption("TTYT Thủy Nguyên · v1.0")

# ─── Page Routing ─────────────────────────────────────────────────────────────

if page == "📊 Tổng quan":
    from views.overview import render
    render()
elif page == "⚙️ Cài đặt":
    from views.settings import render
    render()
