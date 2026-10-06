# Data Card v0.2 — Math Data Lake (Nhóm 1)

*Phiên bản 0.2 (tuần 6). Thay đổi so với v0.1: kho curated thực tế, cập nhật gia tăng, catalog, số liệu chất lượng trên toàn bộ dữ liệu, sửa bộ tách phát biểu Lean. Mọi số liệu lấy từ `catalog/catalog.json` và raw results.*

## 1. Mục đích và người dùng

Kho dữ liệu toán học đa nguồn, đa biểu diễn (văn bản, LaTeX, Lean 3, Lean 4) có lược đồ chung `math_record` v1.0 và provenance tới từng dòng raw — đầu vào chung cho Nhóm 2–8 (xem Data Contract).

## 2. Thành phần (kho hiện hành)

| Nguồn | Phiên bản | Split | Bản ghi trong kho | Dung lượng (Parquet zstd) | Giấy phép |
|---|---|---|---|---|---|
| NuminaMath-CoT | hf-9d8d210c | train, test | 859.594 | 414,1 MB | Apache-2.0 |
| LeanDojo Benchmark 4 | v10-29dcec07 (mathlib4 29dcec07) | train, val, test (random) | 122.512 | 26,9 MB | CC BY 2.0 |
| ProofNet | git-509ad797 | valid, test | 371 | 0,2 MB | MIT |
| **Tổng** | | | **982.477** | **441,2 MB** | |

5 bản ghi raw bị loại (LeanDojo, `full_name = null` trong `Mathlib/Tactic/DeprecateMe.lean` và `Batteries/Util/ProofWanted.lean`) — nằm trong bảng `errors` kèm con trỏ raw.

## 3. Thu thập và lưu trữ

- Raw: 19 tệp, 2,14 GB, ghim phiên bản, sha256 trong manifest (`manifest/manifest_full.json`).
- Staging: JSONL UTF-8 NFC, một bản ghi/dòng.
- Curated: Parquet zstd, partition `source/source_version`, tệp ~128 MB, row group 16 MB (kết luận tuần 5).
- Nhật ký nạp `_lake_log/` (mỗi lần nạp một tệp JSON: batch, số mới/không đổi/xung đột, tệp thêm, compaction).

## 4. Xử lý

- Ánh xạ sang lược đồ chung (Spark ETL, parity 100% với bản Python tham chiếu trên toàn bộ dữ liệu).
- `formal_statement` LeanDojo: lấy từ corpus, cắt tại `:=` **ở mức ngoặc 0** (v0.3). Kiểm tra cân bằng ngoặc: lệch 1/122.512 (trước sửa: 4.887).
- Không sửa nội dung LaTeX/Lean; chỉ gắn cờ chất lượng.

## 5. Chất lượng (toàn bộ kho)

| Chỉ số | Giá trị |
|---|---|
| Tỷ lệ lỗi lược đồ | 5 / 982.482 = 0,0005% |
| Provenance đầy đủ (9 cột) | 100% |
| Truy vết mẫu 30 bản ghi về raw (sha256 + nội dung) | 30/30 khớp |
| Join LeanDojo ↔ corpus | 100% |
| W05 `$` lẻ (NuminaMath) | 25.249 (nhiều dương tính giả do ký hiệu tiền tệ) |
| W04 ký tự điều khiển (NuminaMath) | 266 |
| W03 ký tự U+FFFD (NuminaMath) | 5 |
| W01 ProofNet thiếu chứng minh NL | 2 |
| Trùng nội dung chính xác (cùng `content_sha256`) | NuminaMath: 10.312 bản ghi trong 3.671 nhóm — chuyển cho Nhóm 2 xử lý (đo trên kho này bằng `Tuan_08/scripts/phan_tich_loi.py`) |

## 6. Cập nhật và phiên bản

- Nạp gia tăng theo batch: bản ghi mới được thêm; bản ghi trùng khóa và trùng nội dung được bỏ qua (idempotent); trùng khóa nhưng **khác nội dung trong cùng `source_version` bị từ chối** (E07) vì một phiên bản nguồn là bất biến.
- Snapshot nguồn mới ⇒ `source_version` mới ⇒ partition mới, bản cũ giữ nguyên để tái lập kết quả cũ.

## 7. Hạn chế

- Không có giao dịch ACID: trong lúc compaction có khoảnh khắc ngắn tệp cũ và tệp gộp cùng tồn tại (người đọc có thể thấy bản ghi trùng). Iceberg/Delta là hướng mở rộng.
- Nạp lại batch đã nạp vẫn chạy ETL đầy đủ rồi mới bỏ qua (17,6 s); có thể bỏ qua sớm bằng cách lưu sha256 tệp staging trong nhật ký.
- NuminaMath không có ID gốc; ProofNet là Lean 3; 49,8% định lý LeanDojo không có tactic (term-mode).
- Nhãn chất lượng là cảnh báo heuristic, không phải đánh giá thủ công.

## 8. Giấy phép và trích dẫn

Phát hành mã + mẫu nhỏ + manifest; người dùng tự tải dữ liệu đầy đủ bằng script. Ghi công: NuminaMath (AI-MO, Apache-2.0), ProofNet (Azerbayev et al., MIT), LeanDojo (Yang et al., CC BY 2.0), mathlib4 (Apache-2.0).
