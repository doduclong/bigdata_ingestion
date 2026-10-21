# Bảng đóng góp — Nhóm 1 (bản nháp RC, hoàn thiện ở tuần 10)

*Thay `TV1`…`TV7` bằng họ tên, mã sinh viên; điền link issue/pull request trên kho Git của nhóm.*

| TV | Vai trò chính | Dự phòng cho | Module / tệp phụ trách | Minh chứng (tuần) | Phần bảo vệ cá nhân |
|---|---|---|---|---|---|
| TV1 | Điều phối, data contract, tích hợp nhóm khác | TV7 | `docs/data_contract*`, `schema.py`, `__main__.py` (CLI) | đề cương (1), contract v0.1 (2), v1.0 (9), API (10) | lược đồ chung, khóa `record_id`, quy tắc phiên bản |
| TV2 | Thu nhận NuminaMath-CoT | TV3 | `readers.read_numinamath`, `sample.py` | danh mục nguồn (1), mẫu phân tầng (2), phân tích W05 (8) | khóa `shard:row`, ký hiệu tiền tệ |
| TV3 | Thu nhận ProofNet | TV4 | `readers.read_proofnet`, `transform` (ProofNet) | khảo sát (1), Lean 3 vs 4 (2) | ánh xạ cặp NL–formal |
| TV4 | Thu nhận mathlib4/LeanDojo | TV2 | `readers.read_leandojo_*`, `provenance.iter_json_array`, `STMT_PATTERN` | corpus join (2), sửa tách phát biểu (4), truy vết (6) | join corpus, regex mức ngoặc |
| TV5 | Spark ETL | TV6 | `spark_etl.py`, `tests/test_spark_etl.py` | Spark v0.1 + parity (4), thí nghiệm nhân (7) | biểu thức JVM, kiểm trùng khóa, điểm nghẽn |
| TV6 | Lưu trữ và benchmark | TV5 | `storage.py`, `sql_queries.py`, `runlog.py`, `report.py` | baseline (3), layout L0–L6 (5), quy mô (7), ablation (8) | Parquet/partition/tệp nhỏ, phương pháp đo |
| TV7 | QA, data card, tích hợp | TV1 | `transform.validate`, `lake.py`, `catalog.py`, `tests/` | tiêm lỗi (3), catalog + gia tăng (6), data card (2, 6, 9) | mã lỗi, idempotent, catalog |

**Sử dụng AI:** khai báo tại `docs/ai_use_statement.md`.
