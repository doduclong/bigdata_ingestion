# Data Contract v1.0 — `math_record` (Nhóm 1 → Nhóm 2–8)

**Trạng thái:** release candidate 1.0 (tuần 9). **Bản máy đọc:** `docs/data_contract_v1.0.yaml` (sinh tự động từ `src/mdl/schema.py` bằng `scripts/xuat_data_contract.py`).
**Mock input dùng ngay:** `data_sample/curated/math_record_sample.parquet` (997 bản ghi thật, đúng lược đồ, cùng `record_id` với dữ liệu đầy đủ). Tạo lại: `python scripts/mdl.py sample`.

**Thay đổi so với v0.1:** Parquet có row group 16 MB và sắp xếp theo `record_id` trong tệp; thêm mã E07_CONTENT_CONFLICT (nạp gia tăng); `formal_statement` của LeanDojo tách tại `:=` ở mức ngoặc 0 (pipeline ≥ 0.3); kho có nhật ký nạp `_lake_log/`.

## 1. Phạm vi và cam kết

- **Đơn vị dữ liệu:** một dòng = một bài toán+lời giải (NuminaMath), một cặp phát biểu NL–Lean 3 (ProofNet), hoặc một định lý Lean 4 (LeanDojo).
- **Khóa chính:** `(record_id, source_version)`; `record_id = sha1(source + "|" + source_record_key)[:20]`, ổn định qua các lần chạy.
- **Định dạng phát hành:** Parquet (zstd, row group 16 MB, sắp xếp theo `record_id`), chia vùng `source=<..>/source_version=<..>`. Bản mẫu: JSONL + Parquet.
- **Phiên bản nguồn cố định:** NuminaMath `hf-9d8d210c` (Apache-2.0) · ProofNet `git-509ad797` (MIT) · LeanDojo `v10-29dcec07` (CC BY 2.0).

### Bảo đảm (guarantees)

1. 100% bản ghi có đủ provenance: `source, source_version, raw_uri, raw_row, raw_sha256, license, source_url, downloaded_at, ingest_run_id`.
2. Không trùng `(record_id, source_version)`.
3. Văn bản chuẩn hóa Unicode NFC; nội dung LaTeX/Lean **giữ nguyên văn** (Nhóm 2 chịu trách nhiệm chuẩn hóa có kiểm soát).
4. Split giữ nguyên như nguồn; Nhóm 1 không chia lại (split `novel_premises` của LeanDojo nằm trong `extra_json`).
5. Bản ghi vi phạm lỗi cứng không vào curated mà vào bảng `errors` kèm mã lỗi; cảnh báo không chặn nằm trong `quality_flags`.

## 2. Danh sách cột

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

## 3. Mã lỗi và cờ chất lượng

| Mã | Loại | Ý nghĩa |
|---|---|---|
| E01_MISSING_REQUIRED | lỗi cứng | thiếu cột bắt buộc |
| E02_BAD_ENUM | lỗi cứng | giá trị ngoài miền cho phép |
| E03_EMPTY_CONTENT | lỗi cứng | thiếu nội dung tối thiểu theo `record_type` |
| E05_PARSE | lỗi cứng | dòng staging không phải JSON hợp lệ |
| E06_DUPLICATE_KEY | lỗi cứng | trùng khóa chính trong một lần nạp |
| E07_CONTENT_CONFLICT | lỗi cứng | nạp gia tăng: cùng khóa nhưng khác nội dung trong cùng `source_version` — không ghi đè |
| W01_EMPTY_NL_SOLUTION | cảnh báo | cặp NL–formal không có chứng minh NL |
| W02_FORMAL_STATEMENT_MISSING | cảnh báo | định lý LeanDojo không join được với corpus |
| W03_REPLACEMENT_CHAR | cảnh báo | có ký tự U+FFFD |
| W04_CONTROL_CHAR | cảnh báo | có ký tự điều khiển |
| W05_UNBALANCED_DOLLAR | cảnh báo | số dấu `$` lẻ (LaTeX hỏng hoặc ký hiệu tiền tệ) |
| W06_VERY_LONG | cảnh báo | trường văn bản > 50.000 ký tự |

## 4. Cột mỗi nhóm tiêu thụ (đề xuất, cần xác nhận)

| Nhóm | Cột sử dụng |
|---|---|
| 2 — Data Quality | record_id, source, split, nl_problem, nl_solution, formal_statement, content_sha256, raw_uri, raw_row |
| 3, 4 — Retrieval | record_id, lean_full_name, lean_file_path, formal_statement, formal_goal, premises, split, extra_json.split_novel_premises |
| 5 — Autoformalization | record_id, source, nl_problem, formal_statement, formal_language, formal_header, split |
| 6 — Repair | record_id, formal_statement, formal_header, formal_language |
| 7 — Proof search | record_id, lean_full_name, tactics, formal_goal, num_tactics, premises |
| 8 — Tutor | record_id, subset, nl_problem, nl_solution, has_latex |

## 5. Quản lý phiên bản

- **Minor** (thêm cột nullable): tăng `schema_version` 1.x → 1.(x+1), không phá vỡ consumer.
- **Major** (đổi tên/xóa/đổi kiểu cột): 2.0, thông báo trước 1 tuần, giữ bản cũ song song 1 tuần.
- **Dữ liệu mới:** snapshot mới ⇒ `source_version` mới ⇒ partition mới; bản cũ không bị ghi đè.

## 6. Ví dụ truy cập

```
import duckdb
duckdb.sql("SELECT source, split, count(*) FROM 'data_sample/curated/math_record_sample.parquet' GROUP BY ALL")
```
