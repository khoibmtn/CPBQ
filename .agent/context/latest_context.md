# CPBQ Project — Source of Truth
**Last updated:** 2026-02-13 01:46 (conversation c7e54f48)

## Current State
- **Branch:** main
- **Latest tag:** v20260213-0146
- **App:** Streamlit dashboard at localhost:8501
- **Key files:** `views/cost_by_dept.py` (1207 lines)

## Recent Changes (This Session — 2026-02-12 ~ 2026-02-13)

### 1. Column Order Fix
- Refactored `_get_active_columns()` to return a unified list of column definitions preserving `thu_tu` order from profiles
- Modified `_render_comparison_table()` to iterate unified list for headers/data rows

### 2. Ratio Column Feature ("Cột tỷ lệ")
- Added checkbox next to profile dropdown (auto-disables with < 2 periods)
- Added helper functions: `_get_col_raw_value()`, `_fmt_pct_change()`
- "Tỷ lệ%" column shows `(last/first - 1) × 100%` with green/red color coding

### 3. Excel Export Feature ("📥 Tải Excel")
- New `_export_to_excel()` function (~275 lines) using openpyxl
- Mirrors table structure: merged headers, thin black borders, black text, bold for headers/subtotals/total
- Download button in 3-column layout: Profile dropdown | Checkbox | Download button
- File named `CP_theo_khoa_{period_text}.xlsx`

## Architecture Notes
- `cost_by_dept.py` uses HTML table rendering via `st.markdown(unsafe_allow_html=True)`
- Data from BigQuery view `v_thanh_toan` grouped by ml2 (Ngoại trú / Nội trú) then by khoa
- Profiles stored in `lookup_profiles` BigQuery table, define column order via `thu_tu`
- Column types: `metric` (direct fields), `bq` (calculated averages), `ratio` (numerator/denominator)

## Roadmap (ghi nhận 2026-02-14)
1. **Gộp khoa (dưới dạng profile)** — Thêm chức năng gộp nhiều khoa thành nhóm, quản lý bằng profile
2. **Page "Số liệu toàn viện"** — Trang tổng hợp số liệu toàn bệnh viện
3. **Page "ICD"** — Trang tra cứu/thống kê theo mã ICD
4. **Page "Dự kiến chi"** — Trang dự kiến chi phí
5. **Page "Biểu đồ"** — Trang hiển thị biểu đồ trực quan
