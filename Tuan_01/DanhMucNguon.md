# Danh mục nguồn dữ liệu — Nhóm 1 (Tuần 1)

Số liệu dưới đây được sinh bằng `scripts/khao_sat_nguon.py` trên snapshot đã tải về (kết quả thô: `ket_qua/khao_sat_nguon.json`). Không có số nào nhập tay.

## 1. Tổng quan

| Nguồn | URL | Phiên bản cố định | Định dạng raw | Dung lượng raw | Bản ghi | Giấy phép |
|---|---|---|---|---|---|---|
| NuminaMath-CoT | huggingface.co/datasets/AI-MO/NuminaMath-CoT | commit `9d8d210c9f6a36c8f3cd84045668c9b7800ef517` (2024-11-25) | Parquet, 6 tệp | 1,23 GB | 859.594 (train 859.494 + test 100) | Apache-2.0 (dataset card) |
| ProofNet | github.com/zhangir-azerbayev/ProofNet | commit `509ad79710ed4f46ff5c282ed5640c1aa9ac3f30` | JSONL, 2 tệp | 0,54 MB | 371 (valid 185 + test 186) | MIT |
| LeanDojo Benchmark 4 | zenodo.org/records/12740403 | v10 (2024-07-14), mathlib4 `29dcec074de168ac2bf835a77ef68bbe069194c5`, LeanDojo 2.0.0 | tar.gz → JSON array + JSONL | 68 MB nén / 861 MB giải nén | 122.517 định lý (split random: 118.517/2.000/2.000) + corpus 5.674 tệp, 180.973 premise | CC BY 2.0 (mathlib4: Apache-2.0) |
| **Tổng** | | | | **≈ 2,1 GB** | **982.482** | |

## 2. Trường dữ liệu chính

### NuminaMath-CoT (thống kê trên shard train-00000, 171.899 bản ghi)

| Trường | Kiểu | Tỷ lệ rỗng | Độ dài TB (ký tự) | Độ dài max |
|---|---|---|---|---|
| `source` | string | 0% | 9,3 | 14 |
| `problem` | string (text + LaTeX) | 0% | 251,5 | 4.733 |
| `solution` | string (CoT + LaTeX) | 0% | 1.170,6 | 9.193 |
| `messages` | list<struct<role, content>> | — | trùng nội dung problem/solution | |

- 70,8% đề bài có biểu thức LaTeX.
- Phân bố nguồn con (`source`, toàn bộ 859.594): cn_k12 276.589 · synthetic_math 167.895 · orca_math 153.334 · olympiads 150.576 · synthetic_amc 62.111 · aops_forum 30.195 · math 7.478 · gsm8k 7.345 · amc_aime 4.071.
- **Không có ID gốc** → khóa nguồn đề xuất `split:shard:row`.

### ProofNet (371 bản ghi)

| Trường | Kiểu | Tỷ lệ rỗng | Độ dài TB | Độ dài max |
|---|---|---|---|---|
| `id` | string `Sách\|bài` | 0% | 22,9 | 29 |
| `nl_statement` | string (LaTeX) | 0% | 132,6 | 474 |
| `nl_proof` | string (LaTeX) | 0,54% (2 bản ghi) | 793,7 | 3.926 |
| `formal_statement` | string (Lean 3) | 0% | 149,9 | 351 |
| `src_header` | string (import/open Lean 3) | 0% | 174,8 | 224 |

- 91,9% phát biểu tự nhiên có LaTeX. Sách: Dummit-Foote 87, Munkres 60, Rudin 58, Herstein 47, Axler 28, Artin 28, Ireland-Rosen 21, Shakarchi 16, Pugh 14, Putnam 12.

### LeanDojo Benchmark 4 (122.517 định lý, split `random`)

| Trường | Kiểu | Tỷ lệ rỗng | Ghi chú |
|---|---|---|---|
| `url`, `commit` | string | 0% | luôn là mathlib4 @ `29dcec07` |
| `file_path` | string | 0% | ví dụ `Mathlib/Algebra/Lie/SkewAdjoint.lean` |
| `full_name` | string | 0% | tên đầy đủ, dài TB 29 ký tự |
| `start`, `end` | [dòng, cột] | 0% | |
| `traced_tactics` | list<tactic, annotated_tactic, state_before, state_after> | **49,8%** | định lý chứng minh bằng term-mode không có tactic; TB 4,2 tactic/định lý (khi có) |

- `corpus.jsonl`: 5.674 tệp, 180.973 premise (`full_name`, `code`, `kind`, `start`, `end`) — dùng để lấy **mã nguồn phát biểu Lean** của định lý (join theo `file_path + full_name`; kiểm thử trên tập test: 2.000/2.000 khớp).
- Phân bố theo module: Algebra 19.349 · Data 19.332 · Analysis 13.169 · Topology 11.356 · Order 9.567 · MeasureTheory 7.038 · CategoryTheory 6.400 · …
- Có thêm split `novel_premises` (cùng định lý, chia khác) → lưu vào `extra_json`.

## 3. Nhận xét ảnh hưởng tới thiết kế

1. Ba nguồn có ba kiểu khóa khác nhau → cần `record_id` tổng hợp + giữ `source_record_key` gốc.
2. LeanDojo không có trường "phát biểu" trực tiếp → phải join với corpus (rủi ro không khớp phải được đếm và báo cáo).
3. ProofNet (Lean 3) và LeanDojo (Lean 4) không tương thích cú pháp → cột `formal_language` bắt buộc.
4. NuminaMath chiếm 87,5% số bản ghi → cần **lấy mẫu phân tầng** khi tạo mức 10K/100K để không mất nguồn nhỏ.
5. Tệp JSON mảng lớn của LeanDojo là điểm nghẽn RAM tiềm năng cho baseline Python.
