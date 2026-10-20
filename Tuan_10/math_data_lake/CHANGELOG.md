# CHANGELOG

## 1.0.0 (tuần 10) — bàn giao cuối
- Thêm API dữ liệu (`mdl.api`, `python scripts/mdl.py serve`) và client Python (`mdl.client`) cho Nhóm 2–8; load test 1/10/50 client.
- 25 test (thêm 5 test API).

## 1.0.0-rc1 (tuần 9)
- CLI thống nhất `python scripts/mdl.py`; tái tạo curated sample bằng một lệnh; demo end-to-end.
- Mặc định sắp xếp theo `record_id` trong tệp Parquet; compaction giữ thứ tự khóa.
- Data contract v1.0, data card v1.0, system card, AI-use statement.

## 0.3.0 (tuần 4–8)
- Tách `formal_statement` LeanDojo tại `:=` ở mức ngoặc 0 (lỗi 3,99% → 0,001%).
- Row group 16 MB (tuần 5); kho có nhật ký `_lake_log`, nạp gia tăng, E07, minor compaction (tuần 6).
- Chốt chặn RAM 3,5 GB cho mọi lần chạy.

## 0.2.0 (tuần 2–3)
- Reader 3 nguồn, staging JSONL, lược đồ `math_record` 1.0, baseline Python; đọc JSONL nhị phân để chịu lỗi UTF-8.
