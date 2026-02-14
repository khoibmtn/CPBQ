#!/usr/bin/env python3
# v2026.02.14 – Tailwind-in-Streamlit redesign
"""
app.py - CPBQ Dashboard
========================
Sử dụng: source venv/bin/activate && streamlit run app.py

Giao diện quản lý dữ liệu thanh toán BHYT:
  - Tổng quan: Bảng tổng hợp theo tháng / nội-ngoại trú / CSKCB
  - Cài đặt: Quản lý bảng mã lookup
"""

import streamlit as st
from tw_components import inject_tailwind, override_streamlit_widgets

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

# ─── Tailwind CSS + Widget Overrides ─────────────────────────────────────────

inject_tailwind()
override_streamlit_widgets()


# ─── Sidebar Navigation (Page Menu) ──────────────────────────────────────────

PAGES = [
    {"key": "overview",        "label": "📊  Quản lý số liệu",      "icon": "📊"},
    {"key": "hospital_stats",  "label": "🏛️  Số liệu tổng hợp",    "icon": "🏛️"},
    {"key": "cost_by_dept",    "label": "🏥  Chi phí theo khoa",     "icon": "🏥"},
    {"key": "icd_analysis",    "label": "🔬  Chi phí theo mã bệnh", "icon": "🔬"},
    {"key": "settings",        "label": "⚙️  Cấu hình",             "icon": "⚙️"},
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
st.sidebar.caption("TTYT Thủy Nguyên · v2.0-tw")

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
