# Data Card v0.1 — Math Data Lake (Nhóm 1)

*Phiên bản 0.1 (tuần 2). Các số liệu được đọc từ manifest và kết quả chạy `scripts/doc_thu_nguon.py`, `scripts/tao_mau.py`.*

## 1. Mục đích

Kho dữ liệu toán học nhiều nguồn, có lược đồ thống nhất (`math_record` v1.0) và truy vết được nguồn gốc, làm đầu vào chung cho các nhóm AI4Math (chất lượng dữ liệu, truy hồi premise, autoformalization, sửa lỗi Lean, phân tích proof search, tutor).

## 2. Thành phần

| Nguồn | Phiên bản | Split | Bản ghi | Biểu diễn |
|---|---|---|---|---|
| NuminaMath-CoT | hf-9d8d210c | train / test | 859.494 / 100 | văn bản + LaTeX (đề, lời giải CoT) |
| ProofNet | git-509ad797 | valid / test | 185 / 186 | LaTeX + Lean 3 |
| LeanDojo Benchmark 4 | v10-29dcec07 | train / val / test (random) | 118.517 / 2.000 / 2.000 | Lean 4 (tactic, goal, premise) |
| **Tổng** | | | **982.482** | |

Bảng phụ (staging): corpus LeanDojo 5.674 tệp, 180.973 premise — dùng để lấy mã phát biểu Lean và import.

## 3. Thu thập

- Tải bằng `scripts/tai_du_lieu.py` từ URL **ghim theo commit/phiên bản** (HF revision, Git commit, Zenodo record). Không tải "latest".
- Tệp raw bất biến; sha256 của 19 tệp ghi ở `manifest/manifest_full.json` (2,14 GB). Checksum NuminaMath khớp giá trị LFS do HuggingFace công bố.
- Ngày tải: 2026-10-21 (UTC, theo `downloaded_at` trong manifest).

## 4. Tiền xử lý (đến staging)

- Chuẩn hóa Unicode NFC; giữ nguyên nội dung LaTeX và Lean.
- Đổi cấu trúc LeanDojo `annotated_tactic` (mảng hỗn hợp kiểu) thành `{annotated_tactic, premises[]}` để có kiểu đồng nhất.
- Trường gốc không ánh xạ được đóng gói vào `extra_json` (ví dụ `messages` của NuminaMath khi khác problem/solution; `url, commit, start, end, split_novel_premises` của LeanDojo).

## 5. Mẫu phát hành kèm mã (data_sample/)

- 997 bản ghi: NuminaMath 497 (53 bản ghi × 9 nguồn con + 20 test), ProofNet 200, LeanDojo 300 (250/25/25).
- Chọn bằng hash xác định (không ngẫu nhiên) ⇒ tái tạo đúng bằng một lệnh. Mỗi bản ghi giữ số dòng gốc nên `record_id` và provenance trùng với dữ liệu đầy đủ.
- Kiểm tra mẫu: 0 lỗi cứng; cảnh báo: 22 bản ghi `W05_UNBALANCED_DOLLAR`, 1 bản ghi `W04_CONTROL_CHAR`.

## 6. Giấy phép

| Nguồn | Giấy phép | Ghi chú |
|---|---|---|
| NuminaMath-CoT | Apache-2.0 | Dữ liệu tổng hợp từ nhiều nguồn con (AoPS, cn_k12, AMC/AIME…); khi công bố rộng cần xem điều khoản từng nguồn con. |
| ProofNet | MIT | Kèm tệp LICENSE trong mẫu. |
| LeanDojo Benchmark 4 | CC BY 2.0 | Mã mathlib4 gốc: Apache-2.0. Cần ghi công LeanDojo. |

Nhóm chỉ đưa vào Git bản mẫu nhỏ + manifest + script tải; không đưa toàn bộ dữ liệu.

## 7. Hạn chế đã biết

- NuminaMath không có ID gốc ⇒ khóa `shard:row` phụ thuộc thứ tự tệp; nếu nguồn phát hành lại, phải đối chiếu bằng `content_sha256`.
- ProofNet là Lean 3 (không biên dịch trực tiếp bằng Lean 4).
- 49,8% định lý LeanDojo chứng minh bằng term-mode ⇒ `tactics` rỗng, `formal_proof` null.
- `formal_statement` của LeanDojo tách heuristic từ mã nguồn tại dấu `:=` đầu tiên; với khai báo có `:=` trong tham số mặc định có thể cắt sai (sẽ đo ở tuần 4).
- Cờ `W05_UNBALANCED_DOLLAR` có dương tính giả (ký hiệu tiền tệ `$5`).

## 8. Bảo trì

Chủ sở hữu: Nhóm 1 (TV7 QA/data card, TV1 điều phối). Cập nhật data card ở mỗi thay đổi lược đồ hoặc snapshot; bản tiếp theo v0.2 ở tuần 6 (kèm catalog và cập nhật gia tăng).
