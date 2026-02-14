# CPBQ Project – Source of Truth

## Last Updated: 2026-02-15T00:56+07:00
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

### Redesigned "Quản lý số liệu" Tab
- **Year-based data loading**: Dropdown for year + "Tải dữ liệu" button → on-demand query from `v_thanh_toan` VIEW
- **Full-field table**: All columns from enriched view (ml2, ml4, ten_cskcb, khoa, ma_benh_chinh), excluding upload_timestamp & source_file
- **Instant search**: Text input filters client-side in real-time
- **Configurable search columns**: Popover "⚙️ Cột tìm kiếm" with multiselect (defaults: ho_ten, ma_bn, ma_the, ma_benh, etc.)
- **Row-level checkboxes**: `st.data_editor` with ☑ column for each row
- **Select All**: Checkbox above table to select/deselect all rows on current page
- **Delete selected rows**: Button "🗑️ Xóa N dòng đã chọn" with warning + "XÓA" confirmation
- **Auto-refresh after delete**: Caches cleared, data reloaded from BQ, toast shown after rerun
- **Removed**: Old "Xóa dữ liệu theo kỳ" section completely removed

### New cached functions in overview.py
- `_load_available_years()` — distinct years from main table
- `_load_manage_data(nam_qt)` — full data from VIEW filtered by year

### Key constants
- `_MANAGE_EXCLUDE_COLS = {"upload_timestamp", "source_file"}`
- `_DEFAULT_SEARCH_COLS = ["ho_ten", "ma_bn", "ma_the", "ma_benh", ...]`
- `_ROW_KEY_COLS = ["ma_cskcb", "ma_bn", "ma_loaikcb", "ngay_vao", "ngay_ra"]` (composite key for delete)

## Previous Session Changes
- Revamped Import tab: auto-detection of sheets, row validation, paginated tables, duplicate handling, lookup validation, double-upload prevention
- Reusable `paginated_dataframe()` component in `tw_components.py`
- `_clear_all_caches()` helper for cross-page cache invalidation
- Color scheme redesign for dark theme consistency
