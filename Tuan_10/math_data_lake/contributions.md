# Bảng đóng góp cá nhân — Nhóm 1 (bàn giao cuối)

*Nhóm thay `TV1`…`TV7` bằng họ tên + mã sinh viên, điền link issue/PR và tỷ lệ đóng góp đã thống nhất. Mỗi người phải trả lời được toàn pipeline (xem `docs/bo_cau_hoi_bao_ve.md`).*

| TV | Vai trò chính | Dự phòng | Mã / tài liệu phụ trách | Minh chứng theo tuần | Phần bảo vệ cá nhân | Issue / PR | % |
|---|---|---|---|---|---|---|---|
| TV1 | Điều phối, data contract, API | TV7 | `schema.py`, `docs/data_contract*`, `__main__.py`, `api.py`, `client.py` | W1 đề cương · W2 contract v0.1 · W9 v1.0 · W10 API | lược đồ, khóa, phiên bản, API cho nhóm khác | | |
| TV2 | Thu nhận NuminaMath-CoT | TV3 | `readers.read_numinamath`, `sample.py`, `scales.py` | W1 khảo sát · W2 mẫu phân tầng · W8 phân tích W05 | khóa shard:row, mẫu xác định, dương tính giả `$` | | |
| TV3 | Thu nhận ProofNet | TV4 | `readers.read_proofnet`, ánh xạ ProofNet | W1 khảo sát · W2 Lean 3 vs 4 · W8 lỗi W01/W03 | cặp NL–formal, Lean 3 | | |
| TV4 | Thu nhận LeanDojo | TV2 | `readers.read_leandojo_*`, `STMT_PATTERN`, `provenance.py` | W2 join corpus · W4 sửa tách phát biểu · W6 truy vết | corpus, regex mức ngoặc, đọc mảng JSON theo luồng | | |
| TV5 | Spark ETL | TV6 | `spark_etl.py`, `tests/test_spark_etl.py` | W4 Spark + parity · W7 2/4/8 nhân · W8 phân rã | biểu thức JVM, kiểm trùng, điểm nghẽn | | |
| TV6 | Lưu trữ, benchmark | TV5 | `storage.py`, `sql_queries.py`, `runlog.py`, `report.py`, `load_test_api.py` | W3 baseline · W5 L0–L6 · W7 quy mô · W8 ablation · W10 load test | Parquet, partition, small files, phương pháp đo | | |
| TV7 | QA, data card, tích hợp | TV1 | `transform.validate`, `lake.py`, `catalog.py`, `tests/` | W3 tiêm lỗi · W6 gia tăng + catalog · W2/6/9 data card | mã lỗi, idempotent, catalog, test | | |

Sử dụng AI: `docs/ai_use_statement.md`.
