# Tuần 7 — Thí nghiệm quy mô

**Nhiệm vụ:** Chạy 10K, 100K và toàn bộ dữ liệu; lặp ít nhất 3 lần.
**Minh chứng:** CSV kết quả thô; biểu đồ runtime, throughput, RAM, bytes I/O.

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần | `BaoCao_Tuan07.md` / `.docx` |
| CSV kết quả thô (48 lần chạy) | `results/raw/w7_all_runs.csv` |
| Raw results đầy đủ (Phụ lục B) | `results/raw/runs_baseline.jsonl`, `results/raw/runs_spark.jsonl`; log từng lần `logs/` |
| Bảng tổng hợp | `results/tables/w7_scale_summary.csv`, `results/tables/w7_speedup_full.csv` |
| Biểu đồ (sinh từ raw results) | `results/figures/w7_*.png` |
| Script | `scripts/chay_baseline.py --sql`, `scripts/chay_spark.py --queries`, `scripts/tong_hop_w7.py` |

Lệnh tái tạo: xem mục 6 của báo cáo.
