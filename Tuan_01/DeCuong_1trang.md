# Đề cương 1 trang — Nhóm 1: Math Data Lake (Ingestion & Schema)

**Học phần:** INT4418 — Dữ liệu lớn · **Nhóm:** 1 (7 thành viên) · **Tuần:** 1

**Tên nhóm và đề tài:** Nhóm 1 — Math Data Lake: thu nhận dữ liệu toán học nhiều nguồn vào một lược đồ thống nhất, truy vấn được và truy vết được nguồn gốc (provenance).

**Câu hỏi nghiên cứu:**

1. RQ1 — Có thể hợp nhất dữ liệu văn bản, LaTeX và Lean (NuminaMath-CoT, ProofNet, LeanDojo Benchmark 4) vào một lược đồ chung mà **không làm mất thông tin nguồn gốc** hay không? Đo bằng: tỷ lệ bản ghi có đủ trường provenance (mục tiêu 100%), tỷ lệ lỗi lược đồ (mục tiêu < 1%), khả năng truy ngược từ bản ghi curated về đúng dòng trong tệp raw.
2. RQ2 — Khi dữ liệu tăng từ 10K → 100K → toàn bộ (~982K bản ghi), **định dạng lưu trữ** (JSONL vs Parquet) và **cách chia vùng** (không partition / theo nguồn / theo nguồn + phiên bản) ảnh hưởng thế nào tới thời gian xử lý, RAM, dung lượng và thời gian truy vấn?

**Nút thắt Big Data:** (i) *Đa dạng* — 3 nguồn, 3 định dạng (Parquet, JSONL, mảng JSON), 3 biểu diễn (văn bản, LaTeX, Lean 3/4); (ii) *Khối lượng* — 982.482 bản ghi, ~2,1 GB raw (1,2 GB Parquet nén + 0,86 GB JSON); tệp `random/train.json` của LeanDojo 373 MB là một mảng JSON duy nhất → phải đọc cả tệp vào RAM; (iii) *Chi phí đọc–ghi* và *small-file problem* khi chia vùng; (iv) *Cập nhật gia tăng* khi có snapshot mới.

**Dữ liệu và giấy phép:**

| Nguồn | Phiên bản cố định | Bản ghi | Giấy phép |
|---|---|---|---|
| NuminaMath-CoT (HF `AI-MO/NuminaMath-CoT`) | commit `9d8d210c` | 859.594 | Apache-2.0 |
| ProofNet (GitHub `zhangir-azerbayev/ProofNet`) | commit `509ad797` | 371 | MIT |
| LeanDojo Benchmark 4 (Zenodo 12740403) | v10, mathlib4 `29dcec07` | 122.517 định lý (+180.973 premise) | CC BY 2.0 |

**Baseline:** JSONL thô + chương trình Python tuần tự trên một máy; không chia vùng, không tối ưu định dạng (theo yêu cầu bắt buộc). Cùng dữ liệu, cùng máy, cùng timeout với phương pháp chính.

**Ba mức quy mô/tải:** 10K → 100K → toàn bộ 982K bản ghi (bổ sung mức 500K để vẽ đường cong mượt hơn, khớp báo cáo tuần 2). Mẫu con lấy **phân tầng theo nguồn**, xác định bằng hash (tái lập được). Mỗi cấu hình chạy ≥ 3 lần, báo cáo median và min–max.

**Primary metrics:** (1) **Throughput ETL** (bản ghi/giây, end-to-end raw/staging → curated); (2) **Thời gian truy vấn mẫu** (median trên bộ truy vấn chuẩn bằng DuckDB). *Guardrail:* tỷ lệ lỗi lược đồ và độ đầy đủ provenance (phải = 100%). Chỉ số phụ: peak RAM, dung lượng lưu, bytes đọc/ghi, số tệp.

**Kiến trúc bản nháp:** Raw zone (tệp gốc + checksum + manifest) → Staging (JSONL UTF-8, chuẩn hóa tên trường) → ETL (baseline Python tuần tự / Spark ETL) → Curated Parquet chia vùng theo `source/source_version` → Catalog + data card + bộ truy vấn DuckDB → data contract cho Nhóm 2–7.

**Phân vai (chính / dự phòng):**

| TV | Vai trò chính | Dự phòng cho |
|---|---|---|
| TV1 | Điều phối, data contract, tích hợp với nhóm khác | TV7 |
| TV2 | Thu nhận NuminaMath-CoT | TV3 |
| TV3 | Thu nhận ProofNet | TV4 |
| TV4 | Thu nhận mathlib4 / LeanDojo | TV2 |
| TV5 | Spark ETL | TV6 |
| TV6 | Lưu trữ (Parquet, partition) và benchmark | TV5 |
| TV7 | QA, kiểm thử, data card, tích hợp | TV1 |

**Rủi ro và phương án dự phòng:**

| Rủi ro | Ảnh hưởng | Phương án |
|---|---|---|
| Spark trên Windows thiếu `winutils` | Không ghi được Parquet | Đặt `HADOOP_HOME` cục bộ; dự phòng chạy WSL/Docker |
| LeanDojo là mảng JSON 373 MB | Đỉnh RAM cao, OOM ở máy 8 GB | Chuyển sang JSONL ở staging, đọc theo dòng |
| NuminaMath không có ID gốc | Khó upsert khi có phiên bản mới | Khóa `split:shard:row` + `content_sha256` để đối chiếu |
| ProofNet dùng Lean 3, LeanDojo dùng Lean 4 | Nhầm lẫn khi các nhóm sau dùng | Cột `formal_language` bắt buộc |
| Giấy phép NuminaMath gộp từ nhiều nguồn con | Rủi ro pháp lý khi phát hành | Chỉ phát hành mẫu nhỏ + script tải; ghi license note |
| Phụ thuộc tiến độ nhóm khác | Trễ tích hợp | Phát hành mock snapshot + data contract từ tuần 2 |
| Runtime biến động (Windows nền) | Kết luận sai | Lặp ≥ 3 lần, báo cáo median + min–max, ghi cấu hình máy |
