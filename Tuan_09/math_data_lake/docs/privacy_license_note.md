# Ghi chú quyền riêng tư và giấy phép

## Giấy phép dữ liệu

| Nguồn | Giấy phép | Điều kiện | Cách nhóm tuân thủ |
|---|---|---|---|
| NuminaMath-CoT | Apache-2.0 (dataset card) | giữ thông báo giấy phép; dữ liệu gộp từ nhiều nguồn con (AoPS, cn_k12, AMC/AIME, GSM8K, MATH…) có thể có điều khoản riêng | chỉ phát hành mẫu 497 bản ghi + script tải; cột `license` và `subset` trên từng bản ghi |
| ProofNet | MIT | giữ thông báo bản quyền | kèm `data_sample/raw/proofnet/LICENSE` |
| LeanDojo Benchmark 4 | CC BY 2.0 | ghi công | ghi công trong README/data card; `licenses/README.md` của nguồn kèm mẫu |
| mathlib4 (mã Lean trong LeanDojo) | Apache-2.0 | giữ thông báo | ghi trong data card |

Mã nguồn của nhóm: dùng cho mục đích học tập trong học phần INT4418 (nhóm có thể chọn MIT khi công bố).

## Quyền riêng tư

- Dữ liệu là bài toán, lời giải và mã nguồn công khai; không chứa thông tin định danh cá nhân ngoài tên người ra đề trong một số đề thi công khai (AoPS).
- Không thu thập dữ liệu người dùng; không cần ẩn danh hóa.
- Nhóm không đưa dữ liệu đầy đủ lên Git; chỉ mẫu nhỏ + manifest + script tải.
