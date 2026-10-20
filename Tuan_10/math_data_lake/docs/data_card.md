# Data Card v1.0 — Math Data Lake (Nhóm 1, INT4418)

*Theo khung "Datasheets for Datasets". Mọi số liệu lấy từ manifest, catalog và raw results trong `results/raw/`.*

## 1. Động cơ

- **Mục đích:** hợp nhất dữ liệu toán học văn bản/LaTeX (NuminaMath-CoT), cặp NL–Lean 3 (ProofNet) và định lý Lean 4 (LeanDojo Benchmark 4) vào một lược đồ chung, truy vấn được và truy vết được nguồn gốc, làm đầu vào chung cho các nhóm AI4Math.
- **Người tạo:** Nhóm 1 — INT4418 Dữ liệu lớn, PTIT. **Kinh phí:** không.

## 2. Thành phần

| Nguồn | Phiên bản ghim | Split | Bản ghi trong kho | Biểu diễn | Giấy phép |
|---|---|---|---|---|---|
| NuminaMath-CoT | HF revision `9d8d210c` | train 859.494 / test 100 | 859.594 | văn bản + LaTeX | Apache-2.0 |
| ProofNet | Git `509ad797` | valid 185 / test 186 | 371 | LaTeX + Lean 3 | MIT |
| LeanDojo Benchmark 4 | Zenodo v10, mathlib4 `29dcec07` | random: train/val/test | 122.512 | Lean 4 (phát biểu, tactic, goal, premise) | CC BY 2.0 |
| **Tổng** | | | **982.477** (5 bản ghi raw bị loại) | | |

- Một bản ghi = một bài toán + lời giải / một cặp NL–Lean / một định lý Lean. Lược đồ `math_record` v1.0: 37 cột (`docs/data_contract_v1.0.yaml`).
- Không có dữ liệu cá nhân nhạy cảm; một số đề AoPS ghi tên người ra đề (thông tin công khai).
- Mất cân bằng: NuminaMath chiếm 87,5% số bản ghi.

## 3. Thu thập

Tải tự động từ URL ghim phiên bản (`python scripts/mdl.py download`) ngày 2026-10-21; 19 tệp raw, 2,14 GB; sha256 trong `manifest/manifest_full.json` (checksum NuminaMath khớp giá trị LFS do HuggingFace công bố).

## 4. Tiền xử lý

| Bước | Nội dung |
|---|---|
| Staging | JSONL một bản ghi/dòng, Unicode NFC, con trỏ `raw_uri/raw_row` |
| Ánh xạ | Spark ETL bằng biểu thức JVM; parity 100% với bản Python tham chiếu trên toàn bộ 982.477 bản ghi |
| Lean 4 | phát biểu lấy từ corpus LeanDojo, cắt tại `:=` ở mức ngoặc 0 (lệch ngoặc 1/122.512) |
| Không làm | không sửa nội dung LaTeX/Lean, không khử trùng, không chia lại split (thuộc Nhóm 2) |

## 5. Chất lượng

| Chỉ số | Giá trị |
|---|---|
| Tỷ lệ lỗi lược đồ | 0,0005% (5 định lý LeanDojo `full_name = null` — cú pháp lệnh bị trích nhầm) |
| Provenance đầy đủ | 100%; truy vết 30/30 bản ghi mẫu về đúng dòng raw, sha256 khớp |
| W05 số `$` lẻ | 25.249 (≥ 95% là ký hiệu tiền tệ — dương tính giả) |
| W04 ký tự điều khiển | 266 (chủ yếu ligature font TeX OT1 0x0B/0x0C trong aops_forum) |
| W03 U+FFFD | 5 · W01 ProofNet thiếu chứng minh NL: 2 |
| Trùng nội dung chính xác | NuminaMath 10.312 bản ghi / 3.671 nhóm; LeanDojo 1.505 / 720 nhóm (cùng mã phát biểu khác namespace) |

## 6. Sử dụng

- **Phù hợp:** truy hồi premise (Nhóm 3, 4), autoformalization (Nhóm 5, ProofNet), phân tích chất lượng/khử trùng (Nhóm 2), kho bài cho tutor (Nhóm 8).
- **Không phù hợp:** dùng trực tiếp làm benchmark đánh giá khi chưa khử trùng/rò rỉ (Nhóm 2); biên dịch phát biểu ProofNet bằng Lean 4 (là Lean 3).

## 7. Phân phối và bảo trì

Phát hành mã + mẫu 997 bản ghi + manifest; người dùng tải dữ liệu đầy đủ bằng script. Cập nhật gia tăng theo batch (`mdl ingest`), snapshot mới ⇒ `source_version` mới. Liên hệ: TV1 (điều phối), TV7 (QA/data card).
