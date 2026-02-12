#!/usr/bin/env python3
"""
upload_to_bigquery.py - Upload dữ liệu BHYT từ Excel lên BigQuery
===================================================================
Sử dụng: source venv/bin/activate && python upload_to_bigquery.py CPBQ.xlsx

Tính năng:
  - Đọc file Excel, chuẩn hóa kiểu dữ liệu
  - Tự động tạo dataset/table nếu chưa có
  - Check trùng lặp row-level theo (ma_cskcb + ma_bn + ma_loaikcb + ngay_vao + ngay_ra)
  - Thêm metadata: upload_timestamp, source_file
"""

import sys
import os
from datetime import datetime

import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

from config import PROJECT_ID, DATASET_ID, TABLE_ID, FULL_TABLE_ID, LOCATION, SHEET_NAME
from auth import get_credentials


# ─── BigQuery Schema ──────────────────────────────────────────────────────────

SCHEMA = [
    bigquery.SchemaField("stt", "INT64"),
    bigquery.SchemaField("ma_bn", "STRING"),
    bigquery.SchemaField("ho_ten", "STRING"),
    bigquery.SchemaField("ngay_sinh", "DATE"),
    bigquery.SchemaField("gioi_tinh", "INT64"),
    bigquery.SchemaField("dia_chi", "STRING"),
    bigquery.SchemaField("ma_the", "STRING"),
    bigquery.SchemaField("ma_dkbd", "STRING"),
    bigquery.SchemaField("gt_the_tu", "DATE"),
    bigquery.SchemaField("gt_the_den", "DATE"),
    bigquery.SchemaField("ma_benh", "STRING"),
    bigquery.SchemaField("ma_benhkhac", "STRING"),
    bigquery.SchemaField("ma_lydo_vvien", "INT64"),
    bigquery.SchemaField("ma_noi_chuyen", "STRING"),
    bigquery.SchemaField("ngay_vao", "DATETIME"),
    bigquery.SchemaField("ngay_ra", "DATETIME"),
    bigquery.SchemaField("so_ngay_dtri", "INT64"),
    bigquery.SchemaField("ket_qua_dtri", "INT64"),
    bigquery.SchemaField("tinh_trang_rv", "INT64"),
    bigquery.SchemaField("t_tongchi", "FLOAT64"),
    bigquery.SchemaField("t_xn", "FLOAT64"),
    bigquery.SchemaField("t_cdha", "FLOAT64"),
    bigquery.SchemaField("t_thuoc", "FLOAT64"),
    bigquery.SchemaField("t_mau", "FLOAT64"),
    bigquery.SchemaField("t_pttt", "FLOAT64"),
    bigquery.SchemaField("t_vtyt", "FLOAT64"),
    bigquery.SchemaField("t_dvkt_tyle", "FLOAT64"),
    bigquery.SchemaField("t_thuoc_tyle", "FLOAT64"),
    bigquery.SchemaField("t_vtyt_tyle", "FLOAT64"),
    bigquery.SchemaField("t_kham", "FLOAT64"),
    bigquery.SchemaField("t_giuong", "FLOAT64"),
    bigquery.SchemaField("t_vchuyen", "FLOAT64"),
    bigquery.SchemaField("t_bntt", "FLOAT64"),
    bigquery.SchemaField("t_bhtt", "FLOAT64"),
    bigquery.SchemaField("t_ngoaids", "FLOAT64"),
    bigquery.SchemaField("ma_khoa", "STRING"),
    bigquery.SchemaField("nam_qt", "INT64"),
    bigquery.SchemaField("thang_qt", "INT64"),
    bigquery.SchemaField("ma_khuvuc", "STRING"),
    bigquery.SchemaField("ma_loaikcb", "INT64"),
    bigquery.SchemaField("ma_cskcb", "STRING"),
    bigquery.SchemaField("noi_ttoan", "INT64"),
    bigquery.SchemaField("giam_dinh", "STRING"),
    bigquery.SchemaField("t_xuattoan", "FLOAT64"),
    bigquery.SchemaField("t_nguonkhac", "FLOAT64"),
    bigquery.SchemaField("t_datuyen", "FLOAT64"),
    bigquery.SchemaField("t_vuottran", "FLOAT64"),
    # Metadata columns
    bigquery.SchemaField("upload_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("source_file", "STRING"),
]

# Composite key xác định 1 đợt điều trị duy nhất của bệnh nhân
ROW_KEY_COLS = ["ma_cskcb", "ma_bn", "ma_loaikcb", "ngay_vao", "ngay_ra"]


# ─── Data Transformation ──────────────────────────────────────────────────────

def parse_date_int(val):
    """Chuyển int YYYYMMDD → datetime.date, trả None nếu lỗi."""
    if pd.isna(val):
        return None
    try:
        s = str(int(val))
        return datetime.strptime(s, "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


def parse_datetime_str(val):
    """Chuyển string '202601020735' → datetime, trả None nếu lỗi."""
    if pd.isna(val):
        return None
    try:
        s = str(val).strip().lstrip("'")
        if len(s) == 12:
            return datetime.strptime(s, "%Y%m%d%H%M")
        elif len(s) == 14:
            return datetime.strptime(s, "%Y%m%d%H%M%S")
        elif len(s) == 8:
            return datetime.strptime(s, "%Y%m%d")
        return None
    except (ValueError, TypeError):
        return None


def transform_dataframe(df: pd.DataFrame, source_filename: str) -> pd.DataFrame:
    """Chuẩn hóa kiểu dữ liệu cho tất cả các cột."""
    print("  ⏳ Chuẩn hóa dữ liệu...")

    # Lowercase all column names
    df.columns = [c.lower().strip() for c in df.columns]

    # Date columns: YYYYMMDD int → date
    for col in ["ngay_sinh", "gt_the_tu", "gt_the_den"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_date_int)

    # Datetime columns: string → datetime
    for col in ["ngay_vao", "ngay_ra"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_datetime_str)

    # String columns: ensure str type
    str_cols = ["ma_bn", "ma_the", "ma_dkbd", "ma_benh", "ma_benhkhac",
                "ma_noi_chuyen", "ma_khoa", "ma_khuvuc", "ma_cskcb",
                "giam_dinh", "ho_ten", "dia_chi"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) and x != "" else None)
            # Clean 'nan' strings
            df[col] = df[col].replace("nan", None)

    # Float columns: ensure float type
    float_cols = ["t_tongchi", "t_xn", "t_cdha", "t_thuoc", "t_mau",
                  "t_pttt", "t_vtyt", "t_dvkt_tyle", "t_thuoc_tyle",
                  "t_vtyt_tyle", "t_kham", "t_giuong", "t_vchuyen",
                  "t_bntt", "t_bhtt", "t_ngoaids", "t_xuattoan",
                  "t_nguonkhac", "t_datuyen", "t_vuottran"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Int columns: coerce to int
    int_cols = ["stt", "gioi_tinh", "ma_lydo_vvien", "so_ngay_dtri",
                "ket_qua_dtri", "tinh_trang_rv", "nam_qt", "thang_qt",
                "ma_loaikcb", "noi_ttoan"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add metadata columns
    df["upload_timestamp"] = datetime.utcnow()
    df["source_file"] = source_filename

    print(f"  ✅ Chuẩn hóa xong: {len(df)} dòng")
    return df


# ─── BigQuery Operations ──────────────────────────────────────────────────────

def ensure_dataset(client: bigquery.Client):
    """Tạo dataset nếu chưa tồn tại."""
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        client.get_dataset(dataset_ref)
        print(f"  ✅ Dataset '{DATASET_ID}' đã tồn tại")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = LOCATION
        dataset.description = "Dữ liệu chi phí bảo quản BHYT - TTYT Thủy Nguyên"
        client.create_dataset(dataset)
        print(f"  ✅ Đã tạo dataset '{DATASET_ID}' tại {LOCATION}")


def ensure_table(client: bigquery.Client):
    """Tạo table nếu chưa tồn tại."""
    try:
        client.get_table(FULL_TABLE_ID)
        print(f"  ✅ Table '{TABLE_ID}' đã tồn tại")
    except NotFound:
        table = bigquery.Table(FULL_TABLE_ID, schema=SCHEMA)
        table.description = "Dữ liệu thanh toán BHYT hàng tháng"
        # Partition by thang_qt for efficient querying
        table.range_partitioning = bigquery.RangePartitioning(
            field="thang_qt",
            range_=bigquery.PartitionRange(start=1, end=13, interval=1),
        )
        table.clustering_fields = ["ma_cskcb", "ma_bn"]
        client.create_table(table)
        print(f"  ✅ Đã tạo table '{TABLE_ID}'")


def check_duplicates(client: bigquery.Client, df: pd.DataFrame) -> pd.DataFrame:
    """
    Kiểm tra trùng lặp ở cấp từng dòng (row-level).
    Sử dụng 2-stage approach:
      Stage 1: Lọc theo ma_bn (mã bệnh nhân) → tìm tất cả lượt KCB của cùng BN
      Stage 2: Merge chính xác theo composite key (ma_cskcb, ma_bn, ma_loaikcb, ngay_vao, ngay_ra)
    Trả về DataFrame chứa các dòng trùng (từ df gốc), hoặc DataFrame rỗng.
    """
    try:
        client.get_table(FULL_TABLE_ID)
    except NotFound:
        return pd.DataFrame()  # Table chưa tồn tại → không trùng

    # ── Stage 1: Lọc theo mã bệnh nhân ──
    ma_bn_list = df["ma_bn"].dropna().unique().tolist()
    if not ma_bn_list:
        return pd.DataFrame()

    # Chia batch nếu danh sách BN quá lớn (BigQuery giới hạn query size)
    BATCH_SIZE = 5000
    key_cols_sql = ", ".join(ROW_KEY_COLS)
    all_bq_rows = []

    for i in range(0, len(ma_bn_list), BATCH_SIZE):
        batch = ma_bn_list[i:i + BATCH_SIZE]
        ma_bn_in = ", ".join([f"'{str(m)}'" for m in batch])
        query = f"""
            SELECT {key_cols_sql}
            FROM `{FULL_TABLE_ID}`
            WHERE ma_bn IN ({ma_bn_in})
        """
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(ma_bn_list) + BATCH_SIZE - 1) // BATCH_SIZE
        if total_batches > 1:
            print(f"  ⏳ Đang truy vấn BigQuery (batch {batch_num}/{total_batches})...")
        else:
            print("  ⏳ Đang truy vấn BigQuery để so sánh...")
        result = client.query(query).to_dataframe()
        if not result.empty:
            all_bq_rows.append(result)

    if not all_bq_rows:
        return pd.DataFrame()

    bq_rows = pd.concat(all_bq_rows, ignore_index=True)

    if bq_rows.empty:
        return pd.DataFrame()

    # ── Stage 2: Merge chính xác theo composite key ──
    # Chuẩn hóa kiểu dữ liệu để merge chính xác
    merge_df = df[ROW_KEY_COLS].copy()
    for col in ["ma_cskcb", "ma_bn"]:
        merge_df[col] = merge_df[col].astype(str)
        bq_rows[col] = bq_rows[col].astype(str)
    for col in ["ma_loaikcb"]:
        merge_df[col] = pd.to_numeric(merge_df[col], errors="coerce")
        bq_rows[col] = pd.to_numeric(bq_rows[col], errors="coerce")
    for col in ["ngay_vao", "ngay_ra"]:
        merge_df[col] = pd.to_datetime(merge_df[col], errors="coerce")
        bq_rows[col] = pd.to_datetime(bq_rows[col], errors="coerce")

    # Đánh dấu dòng nào trùng bằng merge indicator
    merged = merge_df.merge(bq_rows, on=ROW_KEY_COLS, how="inner")

    if merged.empty:
        return pd.DataFrame()

    # Trả về index của các dòng trùng trong df gốc
    # Merge lại với df để lấy đúng index
    dup_mask = df[ROW_KEY_COLS].apply(tuple, axis=1).isin(
        merged[ROW_KEY_COLS].apply(tuple, axis=1)
    )
    return df[dup_mask]


def upload_data(client: bigquery.Client, df: pd.DataFrame):
    """Upload DataFrame lên BigQuery."""
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    print(f"  ⏳ Đang upload {len(df)} dòng lên {FULL_TABLE_ID}...")
    job = client.load_table_from_dataframe(df, FULL_TABLE_ID, job_config=job_config)
    job.result()  # Wait for completion

    table = client.get_table(FULL_TABLE_ID)
    print(f"  ✅ Upload thành công! Tổng số dòng trên BigQuery: {table.num_rows}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("❌ Cách dùng: python upload_to_bigquery.py <đường_dẫn_file_excel>")
        print("   Ví dụ: python upload_to_bigquery.py CPBQ.xlsx")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ Không tìm thấy file: {filepath}")
        sys.exit(1)

    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"📊 UPLOAD DỮ LIỆU BHYT LÊN BIGQUERY")
    print(f"{'='*60}")
    print(f"  📁 File: {filename}")
    print(f"  🎯 Target: {FULL_TABLE_ID}")
    print(f"  📍 Location: {LOCATION}")
    print()

    # ── Step 1: Read Excel ──
    print("📖 Bước 1: Đọc file Excel...")
    try:
        df = pd.read_excel(filepath, sheet_name=SHEET_NAME, engine="openpyxl")
        print(f"  ✅ Đọc được {len(df)} dòng, {len(df.columns)} cột từ sheet '{SHEET_NAME}'")
    except Exception as e:
        print(f"  ❌ Lỗi đọc file: {e}")
        sys.exit(1)

    # ── Step 2: Transform data ──
    print("\n🔄 Bước 2: Chuẩn hóa dữ liệu...")
    df = transform_dataframe(df, filename)

    # Show summary
    combos = df[["nam_qt", "thang_qt", "ma_cskcb"]].drop_duplicates()
    print(f"\n  📋 Tóm tắt dữ liệu:")
    for _, row in combos.iterrows():
        subset = df[(df["nam_qt"] == row["nam_qt"]) &
                     (df["thang_qt"] == row["thang_qt"]) &
                     (df["ma_cskcb"] == row["ma_cskcb"])]
        print(f"     - {int(row['thang_qt']):02d}/{int(row['nam_qt'])} | "
              f"CSKCB: {row['ma_cskcb']} | "
              f"{len(subset)} dòng | "
              f"Tổng chi: {subset['t_tongchi'].sum():,.0f} VND")

    # ── Step 3: Connect to BigQuery ──
    print("\n🔗 Bước 3: Kết nối BigQuery...")
    try:
        creds = get_credentials()
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION, credentials=creds)
        print(f"  ✅ Đã kết nối project '{PROJECT_ID}'")
    except Exception as e:
        print(f"  ❌ Lỗi kết nối: {e}")
        print("  💡 Kiểm tra file credentials/client_secret.json")
        sys.exit(1)

    # ── Step 4: Ensure dataset & table ──
    print("\n📦 Bước 4: Kiểm tra dataset & table...")
    ensure_dataset(client)
    ensure_table(client)

    # ── Step 5: Check duplicates ──
    print("\n🔍 Bước 5: Kiểm tra trùng lặp (row-level)...")
    print(f"  🔑 Composite key: {' + '.join(ROW_KEY_COLS)}")
    dup_df = check_duplicates(client, df)

    if not dup_df.empty:
        # Thống kê trùng theo tháng/CSKCB
        dup_summary = dup_df.groupby(["nam_qt", "thang_qt", "ma_cskcb"]).size().reset_index(name="so_dong")
        print(f"  ⚠️  Phát hiện {len(dup_df)}/{len(df)} dòng đã tồn tại trên BigQuery:")
        for _, row in dup_summary.iterrows():
            print(f"     - {int(row['thang_qt']):02d}/{int(row['nam_qt'])} | "
                  f"CSKCB: {row['ma_cskcb']} | {row['so_dong']} dòng trùng")

        new_count = len(df) - len(dup_df)
        print(f"  ℹ️  Dòng mới (chưa có trên BQ): {new_count}")

        choice = input("\n  Bạn muốn:\n"
                       "    [1] Bỏ qua phần trùng, chỉ upload phần mới\n"
                       "    [2] Upload tất cả (cho phép trùng)\n"
                       "    [3] Xóa dữ liệu trùng cũ rồi upload lại tất cả\n"
                       "    [0] Hủy\n"
                       "  Chọn (0/1/2/3): ").strip()

        if choice == "0":
            print("\n  ❌ Đã hủy upload.")
            sys.exit(0)
        elif choice == "1":
            # Lọc chính xác từng dòng trùng, giữ lại dòng mới
            dup_keys = set(dup_df[ROW_KEY_COLS].apply(tuple, axis=1))
            df = df[~df[ROW_KEY_COLS].apply(tuple, axis=1).isin(dup_keys)]
            if len(df) == 0:
                print("\n  ℹ️  Không còn dữ liệu mới để upload.")
                sys.exit(0)
            print(f"\n  ℹ️  Còn lại {len(df)} dòng mới để upload.")
        elif choice == "3":
            # Xóa chính xác từng nhóm dòng trùng trên BigQuery
            dup_groups = dup_df.groupby(["nam_qt", "thang_qt", "ma_cskcb"])
            for (nam, thang, cskcb), group in dup_groups:
                # Build conditions cho từng dòng trùng trong nhóm
                row_conditions = []
                for _, r in group.iterrows():
                    ngay_vao_str = r["ngay_vao"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(r["ngay_vao"]) else None
                    ngay_ra_str = r["ngay_ra"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(r["ngay_ra"]) else None
                    parts = [f"ma_cskcb = '{r['ma_cskcb']}'",
                             f"ma_bn = '{r['ma_bn']}'"]
                    parts.append(f"ma_loaikcb = {int(r['ma_loaikcb'])}" if pd.notna(r["ma_loaikcb"]) else "ma_loaikcb IS NULL")
                    parts.append(f"ngay_vao = '{ngay_vao_str}'" if ngay_vao_str else "ngay_vao IS NULL")
                    parts.append(f"ngay_ra = '{ngay_ra_str}'" if ngay_ra_str else "ngay_ra IS NULL")
                    row_conditions.append(f"({' AND '.join(parts)})")

                # Xóa theo batch mỗi nhóm tháng/CSKCB
                delete_query = f"""
                    DELETE FROM `{FULL_TABLE_ID}`
                    WHERE nam_qt = {int(nam)} AND thang_qt = {int(thang)}
                      AND ({' OR '.join(row_conditions)})
                """
                client.query(delete_query).result()
                print(f"  🗑️  Đã xóa {len(group)} dòng cũ: {int(thang):02d}/{int(nam)} | CSKCB: {cskcb}")
        # choice == "2": upload all (do nothing)
    else:
        print("  ✅ Không phát hiện trùng lặp.")

    # ── Step 6: Upload ──
    print(f"\n🚀 Bước 6: Upload dữ liệu...")
    upload_data(client, df)

    print(f"\n{'='*60}")
    print(f"🎉 HOÀN THÀNH!")
    print(f"{'='*60}")
    print(f"  Để truy vấn dữ liệu, vào: https://console.cloud.google.com/bigquery?project={PROJECT_ID}")
    print()


if __name__ == "__main__":
    main()
