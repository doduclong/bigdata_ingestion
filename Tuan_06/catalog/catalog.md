# Catalog — kho Math Data Lake (sinh tự động lúc 2026-10-21T13:47:35+00:00)

Bảng `math_record`: 982,477 bản ghi, 441.2 MB, định dạng parquet (zstd, row group 16 MB), partition `source/source_version`, khóa `record_id, source_version`, lược đồ 1.0, pipeline 0.3.0.

## Partition

| Nguồn | Phiên bản | Split | Bản ghi | Tệp | MB | Giấy phép |
|---|---|---|---|---|---|---|
| leandojo | v10-29dcec07 | test,train,val | 122,512 | 1 | 26.9 | CC-BY-2.0 |
| numinamath | hf-9d8d210c | test,train | 859,594 | 10 | 414.1 | Apache-2.0 |
| proofnet | git-509ad797 | test,valid | 371 | 1 | 0.2 | MIT |

## Lịch sử nạp (_lake_log)

| v | Batch | Thời điểm (UTC) | Mới | Không đổi | Xung đột | Tệp thêm | Tổng (s) |
|---|---|---|---|---|---|---|---|
| 0 | v0 nạp ban đầu (trừ NuminaMath shard 4) | 2026-10-21T13:46:30+00:00 | 810,579 | 0 | 0 | 17 | 53.991 |
| 1 | v1 batch mới NuminaMath shard 4 | 2026-10-21T13:46:53+00:00 | 171,898 | 0 | 0 | 5 | 23.104 |
| 2 | v2 nạp lại batch shard 4 (idempotent) | 2026-10-21T13:47:11+00:00 | 0 | 171,898 | 0 | 0 | 18.075 |

## Chất lượng

| Nguồn | Mã | Số bản ghi |
|---|---|---|
| leandojo | E03_EMPTY_CONTENT (lỗi, ngoài kho) | 5 |
| leandojo | E06_DUPLICATE_KEY (lỗi, ngoài kho) | 3 |
| numinamath | W03_REPLACEMENT_CHAR (cảnh báo) | 5 |
| numinamath | W04_CONTROL_CHAR (cảnh báo) | 266 |
| numinamath | W05_UNBALANCED_DOLLAR (cảnh báo) | 25,249 |
| proofnet | W01_EMPTY_NL_SOLUTION (cảnh báo) | 2 |

## Cột

| Cột | Kiểu | Null | Mô tả |
|---|---|---|---|
| `record_id` | string | không | sha1(source + '/' + source_record_key)[:20]; khóa ổn định giữa các lần chạy |
| `source` | string | không | numinamath / proofnet / leandojo (cột partition) |
| `source_version` | string | không | phiên bản snapshot, khớp manifest (cột partition) |
| `source_record_key` | string | không | khóa gốc: id ProofNet / file_path::full_name / shard:row |
| `record_type` | string | không | problem_solution / nl_formal_pair / formal_theorem |
| `split` | string | không | split gốc của nguồn: train/val/valid/test |
| `subset` | string | có | nguồn con (NuminaMath), sách (ProofNet), nhóm module (LeanDojo) |
| `nl_problem` | string | có | đề bài / phát biểu ngôn ngữ tự nhiên (giữ nguyên LaTeX) |
| `nl_solution` | string | có | lời giải / chứng minh ngôn ngữ tự nhiên |
| `formal_language` | string | có | lean3 / lean4 / null |
| `formal_statement` | string | có | phát biểu hình thức (Lean) |
| `formal_proof` | string | có | chứng minh hình thức: các tactic nối bằng xuống dòng |
| `formal_header` | string | có | header/import cần để biên dịch phát biểu |
| `formal_goal` | string | có | goal ban đầu (state_before của tactic đầu tiên) |
| `lean_full_name` | string | có | tên đầy đủ của định lý Lean |
| `lean_file_path` | string | có | đường dẫn tệp .lean trong mathlib4 |
| `lean_start_line` | int | có | dòng bắt đầu khai báo |
| `lean_end_line` | int | có | dòng kết thúc khai báo |
| `tactics` | list<string> | không | danh sách tactic (rỗng nếu không có) |
| `premises` | list<string> | không | tên premise duy nhất được dùng trong chứng minh (theo thứ tự xuất hiện) |
| `num_tactics` | int | không | số tactic |
| `has_text` | bool | không | có nl_problem hoặc nl_solution |
| `has_latex` | bool | không | nội dung NL chứa biểu thức LaTeX |
| `has_lean` | bool | không | có formal_statement |
| `latex_count` | int | không | số biểu thức LaTeX trong nl_problem + nl_solution |
| `content_sha256` | string | không | sha256 của nl_problem␟nl_solution␟formal_statement␟formal_proof |
| `quality_flags` | list<string> | không | cảnh báo chất lượng không chặn (W01..) |
| `extra_json` | string | có | trường gốc chưa ánh xạ (JSON), để không mất thông tin |
| `raw_uri` | string | không | đường dẫn tệp raw (tương đối với kho) |
| `raw_row` | int | không | chỉ số dòng/bản ghi trong tệp raw |
| `raw_sha256` | string | không | sha256 tệp raw, khớp manifest |
| `license` | string | không | SPDX id giấy phép của nguồn |
| `source_url` | string | không | URL trang nguồn |
| `downloaded_at` | string | không | thời điểm tải tệp raw (ISO-8601 UTC) |
| `ingest_run_id` | string | không | mã lần chạy ETL tạo ra bản ghi |
| `pipeline_version` | string | không | phiên bản mã pipeline |
| `schema_version` | string | không | phiên bản lược đồ, hiện tại 1.0 |

## Truy vấn mẫu (DuckDB, `math_record` = read_parquet(... , hive_partitioning=true))

- **Đếm bản ghi theo nguồn và split:** `SELECT source, split, count(*) FROM math_record GROUP BY ALL ORDER BY ALL`
- **Cặp NL–Lean 3 của ProofNet theo sách:** `SELECT subset, count(*) FROM math_record WHERE source = 'proofnet' GROUP BY 1 ORDER BY 2 DESC`
- **Định lý Lean 4 dùng một premise cho trước:** `SELECT lean_full_name, formal_statement FROM math_record WHERE source = 'leandojo' AND list_contains(premises, 'Nat.succ_le_iff')`
- **Truy ngược nguồn gốc một bản ghi:** `SELECT raw_uri, raw_row, raw_sha256, license, downloaded_at, ingest_run_id FROM math_record WHERE record_id = '<id>'`
- **Bài olympiad có LaTeX cho Nhóm 8:** `SELECT record_id, nl_problem FROM math_record WHERE source = 'numinamath' AND subset = 'olympiads' AND has_latex LIMIT 10`
