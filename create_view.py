#!/usr/bin/env python3
"""
create_view.py - Tạo VIEW enriched trên BigQuery
=================================================
Sử dụng: source venv/bin/activate && python create_view.py

Tạo VIEW v_thanh_toan tự động JOIN data gốc với 3 bảng lookup,
thêm 5 cột: ml2, ml4, ten_cskcb, khoa, ma_benh_chinh.

Logic cột 'khoa':
  - Ngoại trú + Khám bệnh        → "Khám bệnh (ten_cskcb)"
  - Ngoại trú + ĐTNT + K35       → short_name từ bảng khoa
  - Ngoại trú + ĐTNT + khác K35  → "Điều trị ngoại trú"
  - Nội trú                       → short_name từ bảng khoa
"""

from google.cloud import bigquery

from config import (
    PROJECT_ID, DATASET_ID, LOCATION, VIEW_ID,
    TABLE_ID, LOOKUP_LOAIKCB_TABLE, LOOKUP_CSKCB_TABLE, LOOKUP_KHOA_TABLE,
)
from auth import get_credentials


def build_view_sql() -> str:
    """Tạo câu SQL cho VIEW."""

    # Validity condition macro: convert nam_qt + thang_qt → YYYYMM01
    # then check valid_from <= date_val AND (valid_to IS NULL OR valid_to >= date_val)
    def validity(alias):
        return (
            f"{alias}.valid_from <= (t.nam_qt * 10000 + t.thang_qt * 100 + 1) "
            f"AND ({alias}.valid_to IS NULL OR {alias}.valid_to >= (t.nam_qt * 10000 + t.thang_qt * 100 + 1))"
        )

    ds = f"`{PROJECT_ID}.{DATASET_ID}"

    sql = f"""
CREATE OR REPLACE VIEW {ds}.{VIEW_ID}` AS
SELECT
  t.*,
  lk.ml2,
  lk.ml4,
  cs.ten_cskcb,
  CASE
    -- Ngoại trú
    WHEN lk.ml2 = 'Ngoại trú' THEN
      CASE
        -- Ngoại trú + Điều trị ngoại trú
        WHEN lk.ml4 = 'Điều trị ngoại trú' THEN
          CASE
            WHEN t.ma_khoa = 'K35' THEN kp.short_name
            ELSE 'Điều trị ngoại trú'
          END
        -- Ngoại trú + Khám bệnh (hoặc loại khác)
        ELSE CONCAT('Khám bệnh (', IFNULL(cs.ten_cskcb, ''), ')')
      END
    -- Nội trú → lookup khoa
    ELSE kp.short_name
  END AS khoa,
  LEFT(t.ma_benh, 3) AS ma_benh_chinh

FROM {ds}.{TABLE_ID}` t

-- JOIN 1: Lookup loại KCB (ml2, ml4)
LEFT JOIN {ds}.{LOOKUP_LOAIKCB_TABLE}` lk
  ON t.ma_loaikcb = lk.ma_loaikcb
  AND {validity('lk')}

-- JOIN 2: Lookup cơ sở KCB (ten_cskcb)
LEFT JOIN {ds}.{LOOKUP_CSKCB_TABLE}` cs
  ON t.ma_cskcb = CAST(cs.ma_cskcb AS STRING)
  AND {validity('cs')}

-- JOIN 3: Lookup khoa (short_name cho Nội trú và K35)
LEFT JOIN {ds}.{LOOKUP_KHOA_TABLE}` kp
  ON t.ma_cskcb = CAST(kp.ma_cskcb AS STRING)
  AND t.ma_khoa = kp.makhoa_xml
  AND {validity('kp')}
"""
    return sql.strip()


def main():
    print(f"\n{'='*60}")
    print(f"🏗️  TẠO VIEW ENRICHED TRÊN BIGQUERY")
    print(f"{'='*60}")
    print(f"  🎯 View: {PROJECT_ID}.{DATASET_ID}.{VIEW_ID}")
    print()

    # Connect
    print("🔗 Kết nối BigQuery...")
    creds = get_credentials()
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION, credentials=creds)
    print(f"  ✅ Đã kết nối project '{PROJECT_ID}'")

    # Build and execute VIEW SQL
    sql = build_view_sql()
    print(f"\n📝 SQL VIEW:")
    print("-" * 40)
    print(sql)
    print("-" * 40)

    print(f"\n⏳ Đang tạo VIEW...")
    client.query(sql).result()
    print(f"  ✅ VIEW '{VIEW_ID}' đã được tạo/cập nhật!")

    # Quick verification
    print(f"\n🔍 Kiểm tra nhanh VIEW...")
    verify_sql = f"""
    SELECT ml2, ml4, ten_cskcb, khoa, ma_benh_chinh, ma_benh, ma_loaikcb, ma_khoa, ma_cskcb
    FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}`
    LIMIT 5
    """
    results = list(client.query(verify_sql).result())
    print(f"  ✅ VIEW trả về {len(results)} rows (sample):")
    for r in results:
        print(f"     ml2={r.ml2}, ml4={r.ml4}, khoa={r.khoa}, ma_benh={r.ma_benh}→{r.ma_benh_chinh}")

    print(f"\n{'='*60}")
    print(f"🎉 HOÀN THÀNH!")
    print(f"{'='*60}")
    print(f"  Query VIEW: SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}`")
    print()


if __name__ == "__main__":
    main()
