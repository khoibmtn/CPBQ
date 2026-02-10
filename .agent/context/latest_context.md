# CPBQ Project - Latest Context (Source of Truth)

## 1. Project Overview
Hệ thống upload và xử lý dữ liệu thanh toán BHYT từ file Excel (`CPBQ.xlsx`) lên Google BigQuery phục vụ báo cáo và phân tích.

## 2. Technical Infrastructure
- **GCP Project**: `cpbq-487004`
- **Region**: `asia-southeast1` (Singapore)
- **BigQuery Dataset**: `cpbq_data`
- **BigQuery Table**: `thanh_toan_bhyt`
- **Python Version**: 3.9+ (venv enabled)

## 3. Data Architecture & Logic
- **Primary Source**: Sheet `TH` trong file Excel.
- **Partitioning**: Bảng được phân vùng theo `thang_qt` (range 1-13).
- **Duplicate Prevention**: Dữ liệu được kiểm tra trùng lặp dựa trên combo: `nam_qt`, `thang_qt`, `ma_cskcb`.
- **Schema Standards**:
  - `ngay_sinh`, `gt_the_tu`, `gt_the_den`: Định dạng `DATE`.
  - `ngay_vao`, `ngay_ra`: Định dạng `DATETIME`.
  - Các cột tiền `t_*`: Định dạng `FLOAT64`.
  - Thêm metadata: `upload_timestamp`, `source_file`.

## 4. UI/UX & Design Standards (Future)
- **Màu sắc**: Ưu tiên Green/Blue (như các project TTYT Thủy Nguyên khác).
- **Typography**: Ưu tiên Google Fonts (Inter/Roboto).
- **Layout**: Dashboard tập trung vào các bộ lọc (Month, Facility, ICD-10).

## 5. Coding & Security Rules
- **Authentication**: Sử dụng OAuth2 Browser Flow (`auth.py`). Token lưu tại `credentials/token.json`.
- **Security**: Không bao giờ commit thư mục `credentials/` và `venv/` (đã có `.gitignore`).
- **Configuration**: Toàn bộ biến môi trường tập trung tại `config.py`.

## 6. Git & Workflow Standards
- **Main Branch**: Nhánh production chính.
- **Context Management**:
  - `latest_context.md`: Chứa kiến trúc và quy tắc sau cùng (Source of Truth).
  - `context-*.md`: Nhật ký phiên làm việc (giữ lại 10 file gần nhất).
- **Sync**: Các thay đổi quan trọng phải được merge vào `main` và gắn tag snapshot.
