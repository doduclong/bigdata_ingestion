# 6. Raw results + biểu đồ

| Thư mục/tệp | Nội dung |
|---|---|
| `raw/tuan_03` … `raw/tuan_10` | Kết quả thô từng lần chạy (JSON Lines theo Phụ lục B: run_id, timestamp, code/data version, máy, phần mềm, tham số, seed/timeout, metric, trạng thái, log) + kết quả kiểm tra (parity, tiêm lỗi, truy vết, phân tích lỗi, pytest, load test API) |
| `raw/tuan_07/w7_all_runs.csv` | CSV thô 48 lần chạy quy mô (baseline + Spark 2/4/8 nhân × 4 mức × 3 lần) |
| `figures/h1…h8*.png` | Hình của báo cáo: kiến trúc, runtime, RAM, truy vấn, lưu trữ, phân rã, gia tăng, API |
| `tables/t_*.csv` | Bảng median/min/max |
| `tao_hinh_bao_cao.py`, `tong_hop_api.py` | Sinh lại toàn bộ hình/bảng từ `raw/` (chạy trong `3_Pipeline_Ingest_ETL`, nơi có `results/raw/` giống hệt) |

Không có số nào nhập tay: mọi hình và bảng được sinh bằng script từ các tệp trong `raw/`.
