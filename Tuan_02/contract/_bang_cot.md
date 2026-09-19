| # | Cột | Kiểu | Null | Mô tả |
|---|---|---|---|---|
| 1 | `record_id` | string | không | sha1(source + '/' + source_record_key)[:20]; khóa ổn định giữa các lần chạy |
| 2 | `source` | string | không | numinamath / proofnet / leandojo (cột partition) Miền: leandojo, numinamath, proofnet. |
| 3 | `source_version` | string | không | phiên bản snapshot, khớp manifest (cột partition) |
| 4 | `source_record_key` | string | không | khóa gốc: id ProofNet / file_path::full_name / shard:row |
| 5 | `record_type` | string | không | problem_solution / nl_formal_pair / formal_theorem Miền: formal_theorem, nl_formal_pair, problem_solution. |
| 6 | `split` | string | không | split gốc của nguồn: train/val/valid/test |
| 7 | `subset` | string | có | nguồn con (NuminaMath), sách (ProofNet), nhóm module (LeanDojo) |
| 8 | `nl_problem` | string | có | đề bài / phát biểu ngôn ngữ tự nhiên (giữ nguyên LaTeX) |
| 9 | `nl_solution` | string | có | lời giải / chứng minh ngôn ngữ tự nhiên |
| 10 | `formal_language` | string | có | lean3 / lean4 / null Miền: lean3, lean4. |
| 11 | `formal_statement` | string | có | phát biểu hình thức (Lean) |
| 12 | `formal_proof` | string | có | chứng minh hình thức: các tactic nối bằng xuống dòng |
| 13 | `formal_header` | string | có | header/import cần để biên dịch phát biểu |
| 14 | `formal_goal` | string | có | goal ban đầu (state_before của tactic đầu tiên) |
| 15 | `lean_full_name` | string | có | tên đầy đủ của định lý Lean |
| 16 | `lean_file_path` | string | có | đường dẫn tệp .lean trong mathlib4 |
| 17 | `lean_start_line` | int | có | dòng bắt đầu khai báo |
| 18 | `lean_end_line` | int | có | dòng kết thúc khai báo |
| 19 | `tactics` | list<string> | không | danh sách tactic (rỗng nếu không có) |
| 20 | `premises` | list<string> | không | tên premise duy nhất được dùng trong chứng minh (theo thứ tự xuất hiện) |
| 21 | `num_tactics` | int | không | số tactic |
| 22 | `has_text` | bool | không | có nl_problem hoặc nl_solution |
| 23 | `has_latex` | bool | không | nội dung NL chứa biểu thức LaTeX |
| 24 | `has_lean` | bool | không | có formal_statement |
| 25 | `latex_count` | int | không | số biểu thức LaTeX trong nl_problem + nl_solution |
| 26 | `content_sha256` | string | không | sha256 của nl_problem␟nl_solution␟formal_statement␟formal_proof |
| 27 | `quality_flags` | list<string> | không | cảnh báo chất lượng không chặn (W01..) |
| 28 | `extra_json` | string | có | trường gốc chưa ánh xạ (JSON), để không mất thông tin |
| 29 | `raw_uri` | string | không | đường dẫn tệp raw (tương đối với kho) |
| 30 | `raw_row` | int | không | chỉ số dòng/bản ghi trong tệp raw |
| 31 | `raw_sha256` | string | không | sha256 tệp raw, khớp manifest |
| 32 | `license` | string | không | SPDX id giấy phép của nguồn |
| 33 | `source_url` | string | không | URL trang nguồn |
| 34 | `downloaded_at` | string | không | thời điểm tải tệp raw (ISO-8601 UTC) |
| 35 | `ingest_run_id` | string | không | mã lần chạy ETL tạo ra bản ghi |
| 36 | `pipeline_version` | string | không | phiên bản mã pipeline |
| 37 | `schema_version` | string | không | phiên bản lược đồ, hiện tại 1.0 |
