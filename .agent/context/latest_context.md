# CPBQ Project - Latest Context (Source of Truth)

## 1. Project Overview
Hệ thống upload và xử lý dữ liệu thanh toán BHYT từ file Excel (`CPBQ.xlsx`) lên Google BigQuery phục vụ báo cáo và phân tích. Bao gồm Streamlit Dashboard để xem tổng quan và quản lý bảng mã.

## 2. Technical Infrastructure
- **GCP Project**: `cpbq-487004`
- **Region**: `asia-southeast1` (Singapore)
- **BigQuery Dataset**: `cpbq_data`
- **BigQuery Table (raw)**: `thanh_toan_bhyt` (partitioned by `thang_qt`, clustered by `ma_cskcb`, `ma_bn`)
- **BigQuery VIEW (enriched)**: `v_thanh_toan`
- **Lookup Tables**: `lookup_loaikcb`, `lookup_cskcb`, `lookup_khoa`
- **Python Version**: 3.9+ (venv enabled)
- **Dashboard**: Streamlit (`streamlit run app.py`)

## 3. Data Architecture & Logic
- **Primary Source**: Sheet `TH` (data mới) và `old` (data cũ) trong file Excel.
- **Partitioning**: Bảng được phân vùng theo `thang_qt` (range 1-13).
- **Clustering**: `ma_cskcb`, `ma_bn` — tăng tốc query trùng lặp.
- **Duplicate Prevention**: Row-level, composite key: `ma_cskcb + ma_bn + ma_loaikcb + ngay_vao + ngay_ra`. 2-stage: Stage 1 filter by `ma_bn`, Stage 2 merge on composite key.
- **Schema Standards**:
  - `ngay_sinh`, `gt_the_tu`, `gt_the_den`: Định dạng `DATE`.
  - `ngay_vao`, `ngay_ra`: Định dạng `DATETIME`.
  - Các cột tiền `t_*`: Định dạng `FLOAT64`.
  - Thêm metadata: `upload_timestamp`, `source_file`.

## 4. VIEW Enrichment (v_thanh_toan)
- **5 cột enriched**: `ml2`, `ml4`, `ten_cskcb`, `khoa`, `ma_benh_chinh`
- **Lookup tables** có `valid_from`/`valid_to` (YYYYMMDD) để quản lý thay đổi theo thời gian.
- **Logic cột khoa**:
  - Ngoại trú + Khám bệnh → "Khám bệnh (ten_cskcb)"
  - Ngoại trú + ĐTNT + K35 → short_name (Thận nhân tạo)
  - Ngoại trú + ĐTNT + khác → "Điều trị ngoại trú"
  - Nội trú → short_name từ bảng khoa
- **`ma_benh_chinh`**: LEFT(ma_benh, 3)

## 5. Dashboard App (Streamlit)
- **Entry point**: `app.py` — sidebar navigation, custom CSS (light/dark mode)
- **Helper**: `bq_helper.py` — cached BigQuery client, query runner
- **Trang Tổng quan** (`views/overview.py`):
  - Year selector (chỉ hiện năm có trong DB)
  - Metric toggle: Số lượt KCB / Tổng chi phí
  - 3 metric cards (Ngoại trú / Nội trú / Tổng)
  - HTML pivot table: multi-level headers (🔵 Ngoại trú / 🟠 Nội trú / TỔNG CỘNG)
  - Chỉ hiện CSKCB có dữ liệu (vd: Minh Đức không có Nội trú → không hiện cột)
  - CSS custom properties cho dark mode
- **Trang Cài đặt** (`views/settings.py`):
  - 3 tabs: Loại KCB, Cơ sở KCB, Khoa
  - Editable data grid (`st.data_editor`)
  - Nút Lưu (WRITE_TRUNCATE) & Tải lại
- **CSKCBs**: 31006 (Trung tâm CS1), 31334 (Minh Đức), 31335 (Quảng Thanh)

## 6. UI/UX & Design Standards
- **Màu sắc**: Blue gradient header, semi-transparent metric cards, dark mode support
- **Typography**: Google Fonts (Inter)
- **Theme**: Hỗ trợ cả light và dark mode (CSS custom properties + `prefers-color-scheme`)

## 7. Coding & Security Rules
- **Authentication**: Sử dụng OAuth2 Browser Flow (`auth.py`). Token lưu tại `credentials/token.json`.
- **Security**: Không bao giờ commit thư mục `credentials/` và `venv/` (đã có `.gitignore`).
- **Data files**: `*.xlsx`, `*.xls` không commit (quá lớn cho GitHub).
- **Configuration**: Toàn bộ biến môi trường tập trung tại `config.py`.

## 8. Key Scripts
- `upload_to_bigquery.py`: Upload data gốc từ Excel lên BigQuery (row-level dedup).
- `upload_lookup.py`: Upload 3 bảng lookup (WRITE_TRUNCATE).
- `create_view.py`: Tạo/cập nhật VIEW enriched.
- `app.py`: Streamlit dashboard entry point.
- `bq_helper.py`: BigQuery connection helper.
- `views/overview.py`: Dashboard trang tổng quan.
- `views/settings.py`: Dashboard trang cài đặt.

## 9. Git & Workflow Standards
- **Main Branch**: Nhánh production chính.
- **Context Management**:
  - `latest_context.md`: Chứa kiến trúc và quy tắc sau cùng (Source of Truth).
  - `context-*.md`: Nhật ký phiên làm việc (giữ lại 10 file gần nhất).
- **Sync**: Các thay đổi quan trọng phải được merge vào `main` và gắn tag snapshot.
