# Bài tập lớn INT4418 — Nhóm 1: Math Data Lake (ingestion/schema)

Mỗi tuần một thư mục, theo bảng nhiệm vụ của Nhóm 1 trong `HuongDan_Bai_Tap_Lon_BigData_INT4418.pdf`. Mỗi thư mục có `README.md` liệt kê minh chứng; báo cáo tuần có cả `.md` và `.docx`.

| Tuần | Thư mục | Nhiệm vụ | Minh chứng chính |
|---|---|---|---|
| 1 | `Tuan_01/` | Khảo sát nguồn, giấy phép, trường; chốt câu hỏi, lược đồ nháp | đề cương 1 trang, danh mục nguồn, sơ đồ lược đồ v0.1, board |
| 2 | `Tuan_02/` | Snapshot, manifest, data contract, 100–1.000 bản ghi mẫu | raw sample 997, checksum, contract v0.1, reader 3 nguồn, data card v0.1 |
| 3 | `Tuan_03/` | Baseline JSONL + Python tuần tự | baseline end-to-end, raw timing, báo cáo lỗi đọc |
| 4 | `Tuan_04/` | Spark ETL, chuẩn hóa, test | Spark v0.1, parity 100%, 15 test, tỷ lệ lỗi 0,0005% |
| 5 | `Tuan_05/` | Parquet, partition, kích thước tệp, small files | 7 cấu hình lưu trữ, bảng tệp/dung lượng/thời gian đọc |
| 6 | `Tuan_06/` | Provenance, catalog, cập nhật gia tăng | data card v0.2, catalog, batch mới 171.898 bản ghi |
| 7 | `Tuan_07/` | 10K/100K/500K/toàn bộ × 3 lần | CSV thô 48 lần chạy, biểu đồ runtime/throughput/RAM/I/O |
| 8 | `Tuan_08/` | Ablation, điểm nghẽn, lỗi | bảng ablation, phân rã thời gian, taxonomy lỗi |
| 9 | `Tuan_09/` | Release candidate, báo cáo bài báo ngắn, demo | `math_data_lake/` 1.0.0-rc1, báo cáo 8 trang, demo script |
| 10 | `Tuan_10/` | API dữ liệu, demo, bàn giao | `math_data_lake/` 1.0.0, API + load test, slide, bảng đóng góp |

**Ngoài thư mục tuần:**
- `_storage/` (không nộp, không đưa lên Git): dữ liệu raw, staging, kết quả trung gian.
- `.venv/`: môi trường Python 3.11.
- `_tools/`: công cụ chuyển Markdown → .docx và script tạo slide.

**Sản phẩm bàn giao theo mục 10 của đề bài:** `SanPhamBanGiao/` (7 thư mục: kho Parquet mẫu + manifest, lược đồ + data dictionary, pipeline, data card + license, bộ truy vấn kiểm tra, raw results + biểu đồ, README + demo).

**Bắt đầu từ:** `SanPhamBanGiao/README.md` hoặc `Tuan_10/math_data_lake/README.md`.
