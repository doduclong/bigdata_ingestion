# Data dictionary — bảng `math_record` (lược đồ 1.0)

Sinh tự động bởi `tao_data_dictionary.py` từ `mdl.schema` và kho `đầy đủ` (982,477 bản ghi). Khóa chính `(record_id, source_version)`; partition `source/source_version`.

## 1. Từ điển cột

| # | Cột | Nhóm | Kiểu | Null | Mô tả | Tỷ lệ null % theo nguồn | Ví dụ |
|---|---|---|---|---|---|---|---|
| 1 | `record_id` | định danh | string | không | sha1(source + '/' + source_record_key)[:20]; khóa ổn định giữa các lần chạy | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `00000378dc968485995d` |
| 2 | `source` | provenance | string | không | numinamath / proofnet / leandojo (cột partition) Miền: leandojo, numinamath, proofnet. | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `numinamath` |
| 3 | `source_version` | provenance | string | không | phiên bản snapshot, khớp manifest (cột partition) | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `hf-9d8d210c` |
| 4 | `source_record_key` | định danh | string | không | khóa gốc: id ProofNet / file_path::full_name / shard:row | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `train-00000-of-00005:78817` |
| 5 | `record_type` | định danh | string | không | problem_solution / nl_formal_pair / formal_theorem Miền: formal_theorem, nl_formal_pair, problem_solution. | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `problem_solution` |
| 6 | `split` | định danh | string | không | split gốc của nguồn: train/val/valid/test | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `train` |
| 7 | `subset` | định danh | string | có | nguồn con (NuminaMath), sách (ProofNet), nhóm module (LeanDojo) | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `cn_k12` |
| 8 | `nl_problem` | nội dung | string | có | đề bài / phát biểu ngôn ngữ tự nhiên (giữ nguyên LaTeX) | leandojo: 100.0; numinamath: 0.0; proofnet: 0.0 | `Given that $a\_i > 0 (i=1,2,…,n)$, examine the following inequalities: \[①a\_1 \cdot \frac…` |
| 9 | `nl_solution` | nội dung | string | có | lời giải / chứng minh ngôn ngữ tự nhiên | leandojo: 100.0; numinamath: 0.0; proofnet: 0.0 | `**Conclusion**: $(a\_1+a\_2+…+a\_n)(\frac {1}{a\_1} + \frac {1}{a\_2} +…+ \frac {1}{a\_n})…` |
| 10 | `formal_language` | nội dung | string | có | lean3 / lean4 / null Miền: lean3, lean4. | leandojo: 0.0; numinamath: 100.0; proofnet: 0.0 | `lean4` |
| 11 | `formal_statement` | nội dung | string | có | phát biểu hình thức (Lean) | leandojo: 0.0; numinamath: 100.0; proofnet: 0.0 | `@[simp] lemma deleteEdges_adj : (G.deleteEdges s).Adj v w ↔ G.Adj v w ∧ ¬s(v, w) ∈ s` |
| 12 | `formal_proof` | nội dung | string | có | chứng minh hình thức: các tactic nối bằng xuống dòng | leandojo: 49.76; numinamath: 100.0; proofnet: 100.0 | `simp only [oangle, map_neg] convert Complex.arg_neg_coe_angle _ exact o.kahler_ne_zero hx …` |
| 13 | `formal_header` | nội dung | string | có | header/import cần để biên dịch phát biểu | leandojo: 0.0; numinamath: 100.0; proofnet: 0.0 | `Mathlib/Data/Sym/Sym2.lean Mathlib/Data/Rel.lean .lake/packages/lean4/src/lean/Init.lean M…` |
| 14 | `formal_goal` | nội dung | string | có | goal ban đầu (state_before của tactic đầu tiên) | leandojo: 49.76; numinamath: 100.0; proofnet: 100.0 | `V : Type u_1 V' : Type u_2 inst✝⁵ : NormedAddCommGroup V inst✝⁴ : NormedAddCommGroup V' in…` |
| 15 | `lean_full_name` | nội dung | string | có | tên đầy đủ của định lý Lean | leandojo: 0.0; numinamath: 100.0; proofnet: 100.0 | `SimpleGraph.deleteEdges_adj` |
| 16 | `lean_file_path` | nội dung | string | có | đường dẫn tệp .lean trong mathlib4 | leandojo: 0.0; numinamath: 100.0; proofnet: 100.0 | `Mathlib/Combinatorics/SimpleGraph/Basic.lean` |
| 17 | `lean_start_line` | nội dung | int | có | dòng bắt đầu khai báo | leandojo: 0.0; numinamath: 100.0; proofnet: 100.0 | `926` |
| 18 | `lean_end_line` | nội dung | int | có | dòng kết thúc khai báo | leandojo: 0.0; numinamath: 100.0; proofnet: 100.0 | `927` |
| 19 | `tactics` | nội dung | list<string> | không | danh sách tactic (rỗng nếu không có) | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `[]` |
| 20 | `premises` | nội dung | list<string> | không | tên premise duy nhất được dùng trong chứng minh (theo thứ tự xuất hiện) | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `[]` |
| 21 | `num_tactics` | dẫn xuất | int | không | số tactic | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `0` |
| 22 | `has_text` | dẫn xuất | bool | không | có nl_problem hoặc nl_solution | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `true` |
| 23 | `has_latex` | dẫn xuất | bool | không | nội dung NL chứa biểu thức LaTeX | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `true` |
| 24 | `has_lean` | dẫn xuất | bool | không | có formal_statement | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `false` |
| 25 | `latex_count` | dẫn xuất | int | không | số biểu thức LaTeX trong nl_problem + nl_solution | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `20` |
| 26 | `content_sha256` | dẫn xuất | string | không | sha256 của nl_problem␟nl_solution␟formal_statement␟formal_proof | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `701a4c2175b2748bf67d94e3908ee8db642107f9126a62d289d040aa9490a1aa` |
| 27 | `quality_flags` | dẫn xuất | list<string> | không | cảnh báo chất lượng không chặn (W01..) | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `[]` |
| 28 | `extra_json` | nội dung | string | có | trường gốc chưa ánh xạ (JSON), để không mất thông tin | leandojo: 0.0; numinamath: 100.0; proofnet: 100.0 | `{"commit":"29dcec074de168ac2bf835a77ef68bbe069194c5","end":[927,50],"split_novel_premises"…` |
| 29 | `raw_uri` | provenance | string | không | đường dẫn tệp raw (tương đối với kho) | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `raw/numinamath/train-00000-of-00005.parquet` |
| 30 | `raw_row` | provenance | int | không | chỉ số dòng/bản ghi trong tệp raw | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `78817` |
| 31 | `raw_sha256` | provenance | string | không | sha256 tệp raw, khớp manifest | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `25c0fa2ca96dd8078470ad1bbc439d0d211fd8b7d22e04abf7f61e9be9bf9ec3` |
| 32 | `license` | provenance | string | không | SPDX id giấy phép của nguồn | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `Apache-2.0` |
| 33 | `source_url` | provenance | string | không | URL trang nguồn | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `https://huggingface.co/datasets/AI-MO/NuminaMath-CoT` |
| 34 | `downloaded_at` | provenance | string | không | thời điểm tải tệp raw (ISO-8601 UTC) | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `2026-10-21T09:36:34+00:00` |
| 35 | `ingest_run_id` | provenance | string | không | mã lần chạy ETL tạo ra bản ghi | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `cli-etl` |
| 36 | `pipeline_version` | nội dung | string | không | phiên bản mã pipeline | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `1.0.0` |
| 37 | `schema_version` | nội dung | string | không | phiên bản lược đồ, hiện tại 1.0 | leandojo: 0.0; numinamath: 0.0; proofnet: 0.0 | `1.0` |

## 2. Ánh xạ trường nguồn → cột chung

| Cột | NuminaMath-CoT | ProofNet | LeanDojo Benchmark 4 |
|---|---|---|---|
| `record_id` | sha1('numinamath|'+key)[:20] | sha1('proofnet|'+id)[:20] | sha1('leandojo|'+file_path::full_name)[:20] |
| `source_record_key` | <shard>:<row> (không có ID gốc) | id | file_path::full_name |
| `split` | tên tệp: train/test | valid/test | random split: train/val/test |
| `subset` | source (cn_k12, olympiads…) | tên sách trong id (phần trước |) | 2 cấp module (Mathlib.Algebra) / gói .lake |
| `nl_problem` | problem | nl_statement | — |
| `nl_solution` | solution | nl_proof | — |
| `formal_language` | — | lean3 | lean4 |
| `formal_statement` | — | formal_statement | corpus.code cắt tại := mức ngoặc 0 |
| `formal_proof` | — | — | các tactic nối bằng xuống dòng |
| `formal_header` | — | src_header | corpus.imports nối bằng xuống dòng |
| `formal_goal` | — | — | traced_tactics[0].state_before |
| `lean_full_name` | — | — | full_name |
| `lean_file_path` | — | — | file_path |
| `lean_start_line` | — | — | start[0] |
| `lean_end_line` | — | — | end[0] |
| `tactics` | [] | [] | traced_tactics[].tactic |
| `premises` | [] | [] | annotated_tactic[1][].full_name (duy nhất, theo thứ tự) |
| `extra_json` | messages nếu khác problem/solution | — | url, commit, start, end, split_novel_premises |

Cột nhóm *dẫn xuất* và *provenance* do pipeline sinh (xem `data_contract.md`).
