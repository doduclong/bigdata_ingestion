# Báo cáo tuần 2 — Snapshot, manifest, data contract và dữ liệu mẫu

**Nhóm 1 — Math Data Lake: Ingestion** · INT4418 Dữ liệu lớn

## 1. Nhiệm vụ và minh chứng

| Yêu cầu tuần 2 | Minh chứng | Trạng thái |
|---|---|---|
| Tải snapshot | `scripts/tai_du_lieu.py`; 19 tệp, 2,14 GB trong vùng raw | Xong |
| Manifest + checksum | `manifest/manifest_full.json`, `manifest/manifest_full.sha256` | Xong |
| Data contract | `DataContract_v0.1.md`, `contract/data_contract_v0.1.yaml` | Bản nháp, chờ nhóm khác xác nhận |
| 100–1.000 bản ghi mẫu | `data_sample/raw` (997 bản ghi raw) + `data_sample/curated` (997 bản ghi lược đồ chung) | Xong |
| Script đọc được cả ba nguồn | `src/mdl/readers.py`, `scripts/doc_thu_nguon.py` | Xong (mẫu và đầy đủ) |
| Data card v0.1 | `DataCard_v0.1.md` | Xong |

## 2. Snapshot và manifest

Mỗi nguồn được ghim theo phiên bản: NuminaMath-CoT revision `9d8d210c`, ProofNet commit `509ad797`, LeanDojo Benchmark 4 v10 (mathlib4 `29dcec07`). Manifest ghi cho từng tệp: `source, source_version, license, source_url, raw_uri, bytes, sha256, downloaded_at`. Lệnh `python scripts/tai_du_lieu.py --verify` kiểm tra lại toàn bộ checksum. Checksum 6 tệp NuminaMath trùng với giá trị LFS do HuggingFace công bố.

## 3. Data unit và partition key

- **Data unit:** một bản ghi `math_record` = một bài toán + lời giải / một cặp NL–Lean / một định lý Lean.
- **Khóa:** `record_id = sha1(source|source_record_key)[:20]`, khóa chính `(record_id, source_version)`.
- **Partition key ở curated:** `source / source_version` (thí nghiệm tuần 5 sẽ so sánh với không partition và partition sâu hơn).

## 4. Reader ba nguồn — kết quả đọc thử thật

| Nguồn | Bản ghi đọc được | Lỗi đọc | Thời gian (s) |
|---|---|---|---|
| NuminaMath-CoT (6 tệp Parquet) | 859.594 | 0 | 15,0 |
| ProofNet (2 tệp JSONL) | 371 | 0 | 0,0 |
| LeanDojo (3 tệp JSON + chỉ mục novel_premises) | 122.517 | 0 | 8,0 |
| LeanDojo corpus (tệp + premise) | 186.647 | 0 | 0,6 |

Số thô: `ket_qua/doc_thu_full.json`, `ket_qua/doc_thu_sample.json`. Máy: i7-12700, 23,8 GB RAM, Windows 11, Python 3.11.

Quan sát: tệp LeanDojo là **mảng JSON** nên phải nạp trọn tệp `random/train.json` (373 MB) vào bộ nhớ trước khi duyệt — đây là điểm nghẽn RAM dự kiến cho baseline. Ở vùng staging, nhóm chuyển mọi nguồn sang **JSONL một bản ghi/dòng** để các bước sau đọc theo luồng.

## 5. Map/worker contract

- **Input:** một tệp staging JSONL của một nguồn (mỗi dòng mang `_source, _source_version, _key, _split, _raw_uri, _raw_row`).
- **Xử lý:** ánh xạ sang `math_record` (`src/mdl/transform.py::to_unified`), gắn provenance từ manifest, tính `content_sha256`, `quality_flags`.
- **Lỗi:** bản ghi vi phạm lỗi cứng (E01–E06) được tách vào `errors` kèm mã lỗi và con trỏ raw; không làm dừng pipeline.
- **Idempotent:** `record_id` xác định từ khóa nguồn; ghi đè theo partition `(source, source_version)` ⇒ chạy lại cùng batch không nhân đôi.

## 6. Dữ liệu mẫu (mock input cho nhóm khác)

997 bản ghi: NuminaMath 497 (phân tầng 9 nguồn con), ProofNet 200, LeanDojo 300. Kết quả chạy qua lược đồ chung: **0 lỗi cứng**, 22 cảnh báo `W05_UNBALANCED_DOLLAR`, 1 cảnh báo `W04_CONTROL_CHAR`. Join LeanDojo ↔ corpus thành công 300/300.

## 7. Giả thuyết điểm nghẽn và kế hoạch tuần 3

- RAM khi đọc mảng JSON LeanDojo; thời gian parse JSON và ghi JSONL ở baseline tuần tự; lệch kích thước bản ghi (lời giải NuminaMath dài TB 1.170 ký tự, tối đa 9.193).
- Tuần 3: baseline JSONL + Python tuần tự end-to-end (raw → staging → curated JSONL), đo runtime, throughput, peak RAM, bytes đọc/ghi ở các mức 10K, 100K, 500K và toàn bộ.

## 8. Việc cần các nhóm khác phản hồi

Nhóm 2–8 xác nhận danh sách cột ở mục 4 của Data Contract. Mock input đã sẵn tại `data_sample/curated/math_record_sample.parquet`.
