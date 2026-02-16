# CPBQ Project – Source of Truth

## Last Updated: 2026-02-17T01:50+07:00
## Git Tag: v20260215-0056

## Project Overview
Streamlit dashboard for BHYT (health insurance) cost analysis backed by BigQuery.

## Architecture
- **Framework**: Streamlit (Python)
- **Database**: Google BigQuery
- **Key files**: `app.py`, `config.py`, `bq_helper.py`, `tw_components.py`
- **Views**: `overview.py`, `hospital_stats.py`, `cost_by_dept.py`, `icd_analysis.py`, `settings.py`
- **Upload**: `upload_to_bigquery.py`, `create_view.py`, `upload_lookup.py`
- **Virtual env**: `./venv`

## Menu Structure (sidebar)
1. Quản lý số liệu (overview.py) — 3 tabs: Số liệu tổng hợp, Quản lý số liệu, Import
2. Số liệu tổng hợp (hospital_stats.py)
3. Chi phí theo khoa (cost_by_dept.py)
4. Chi phí theo mã bệnh (icd_analysis.py)
5. Cấu hình (settings.py)

## Recent Changes (this session)

### Inline Clear Button in Search Inputs
- Removed separate ❌ column from search condition rows
- Injected CSS+JS via `st.components.v1.html` using `window.parent.document` to convert keyword inputs to `type="search"` (native browser X icon)
- Added `search` event listener to dispatch React-compatible events when X is clicked

### Loading Animation (st.status)
- Replaced `st.spinner()` with `st.status()` for "Tải dữ liệu" and BigQuery search
- Shows step-by-step progress (⏳ running → ✅ complete)

### Tab Persistence Across Theme Toggle
- Problem: `st.rerun()` on theme toggle reset `st.tabs()` to first tab
- Solution: JS using browser `sessionStorage` tracks active tab clicks, restores tab after rerun
- Implemented in `render()` function at end of `overview.py`

### Multi-Condition Search Builder
- Year range selector (start/end year) with "Phương pháp" combobox (Auto/RAM/BigQuery)
- Auto threshold: ≤3 years → RAM, >3 years → BigQuery
- Multi-condition search with AND/OR operators, add/delete conditions
- BigQuery direct search for large datasets (`_search_bigquery()`)

## Key Constants
- `_MANAGE_EXCLUDE_COLS = {"upload_timestamp", "source_file"}`
- `_DEFAULT_SEARCH_COLS = ["ho_ten", "ma_bn", "ma_the", "ma_benh", ...]`
- `_ROW_KEY_COLS = ["ma_cskcb", "ma_bn", "ma_loaikcb", "ngay_vao", "ngay_ra"]`
- `_AUTO_THRESHOLD = 3` (years, RAM vs BigQuery cutoff)

## Previous Session Changes
- Row-level checkboxes, Select All, Delete selected rows with confirmation
- Revamped Import tab: auto-detection, validation, pagination, duplicate handling
- Reusable `paginated_dataframe()` in `tw_components.py`
- Color scheme redesign for dark theme consistency
