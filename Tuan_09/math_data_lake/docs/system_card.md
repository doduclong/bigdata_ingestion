# System Card — Math Data Lake 1.0.0-rc1

## 1. Thành phần

| Thành phần | Mã | Vai trò |
|---|---|---|
| Thu nhận | `mdl.manifest`, `scripts/tai_du_lieu.py` | tải ghim phiên bản, sha256, manifest, verify |
| Reader / staging | `mdl.readers`, `mdl.staging` | đọc Parquet / JSONL / mảng JSON → JSONL NFC + con trỏ raw |
| Ánh xạ tham chiếu | `mdl.transform` | bản Python thuần (đặc tả hành vi); baseline dùng trực tiếp |
| Spark ETL | `mdl.spark_etl` | ánh xạ bằng biểu thức Spark SQL, kiểm lỗi E01–E06, ghi Parquet |
| Kho + nạp gia tăng | `mdl.lake`, `mdl.storage` | nhật ký `_lake_log`, idempotent, E07, minor/major compaction |
| Catalog / provenance | `mdl.catalog`, `mdl.provenance` | catalog JSON/MD; truy vết record → dòng raw |
| Truy vấn | `mdl.sql_queries`, `mdl.queries` | 6 truy vấn kiểm tra (DuckDB) + bản Python baseline |
| Đo đạc | `mdl.runlog`, `mdl.report` | bản ghi lần chạy (Phụ lục B), chốt chặn RAM, tổng hợp/biểu đồ |

## 2. Hiệu năng đã đo (toàn bộ 982K bản ghi, i7-12700, giới hạn 4 GB RAM)

| Thao tác | Kết quả (median 3 lần) |
|---|---|
| Raw → staging | 42,4 s, peak RSS 1,5 GB |
| Baseline Python → JSONL | 65,8 s, 14.921 bản ghi/s, 430 MB |
| Spark `local[4]`, driver 2 GB → Parquet | 53,8 s, 18.260 bản ghi/s, 2,7 GB |
| Nạp batch 171.898 bản ghi | 22,3 s (dựng lại toàn bộ 52,5 s) |
| Kho Parquet | 441–447 MB (JSONL 2.341 MB) |
| 6 truy vấn kiểm tra, DuckDB 4 luồng | 0,61 s (JSONL: 6,6 s; Python quét: 52 s) |

## 3. Chế độ lỗi và cách xử lý

| Tình huống | Hành vi |
|---|---|
| Dòng JSON hỏng / sai UTF-8 | vào `read_errors`, pipeline tiếp tục |
| Thiếu trường, sai miền, thiếu nội dung, trùng khóa | vào `errors` với mã E01–E06 |
| Cùng khóa, khác nội dung trong cùng phiên bản | từ chối (E07), kho không đổi |
| Nạp lại batch | idempotent: 0 bản ghi mới |
| Tiến trình vượt 3,5 GB RSS hoặc máy còn < 3 GB trống | chốt chặn dừng lần chạy, ghi trạng thái thất bại |
| Tệp raw bị sửa | `mdl verify` báo sai sha256 |

## 4. Giới hạn

Không có giao dịch ACID (có khoảnh khắc trùng tệp khi minor compaction); một máy `local` mode; kiểm tra trùng khóa quét staging hai lần (+30% thời gian); Spark không tăng tốc quá 4 nhân với heap 2 GB.

## 5. Môi trường

Python 3.11.0, PySpark 4.0.1, Java 21.0.8, DuckDB 1.3.2, pyarrow 21.0.0 (`requirements.lock.txt`). Windows cần `winutils.exe` + `hadoop.dll` (Hadoop 3.4) trong `<storage>/hadoop/bin`.
