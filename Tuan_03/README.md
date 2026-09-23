# Tuần 3 — Baseline JSONL + Python tuần tự

**Nhiệm vụ:** Cài baseline JSONL + Python tuần tự; đo thời gian và dung lượng.
**Minh chứng:** Baseline chạy end-to-end; raw timing; báo cáo lỗi đọc.

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần (gồm báo cáo lỗi đọc) | `BaoCao_Tuan03.md` / `.docx` |
| Mã baseline | `src/mdl/baseline.py`, `src/mdl/queries.py`, `scripts/chay_baseline.py` |
| Raw timing (mỗi dòng = một lần chạy, mẫu Phụ lục B) | `results/raw/runs_baseline.jsonl`, `results/raw/runs_ingest.jsonl` |
| Log từng lần chạy (metric + kết quả truy vấn) | `logs/<run_id>.log` |
| Bảng tổng hợp (median/min/max) | `results/tables/baseline_summary.csv` |
| Biểu đồ sinh bằng script | `results/figures/w3_*.png` |
| Kiểm thử lỗi đọc (tiêm lỗi) | `scripts/kiem_tra_loi_doc.py`, `results/raw/fault_injection.json` |

## Pipeline baseline

```
raw (Parquet/JSONL/JSON)  --tao_staging.py-->  staging JSONL  --chay_baseline.py-->  1 tệp math_record.jsonl
                                                                                     + errors.jsonl + read_errors.jsonl
```

Không partition, không nén, một tiến trình Python, đọc tuần tự từng dòng.

## Lệnh tái tạo

```
cd Tuan_03
../.venv/Scripts/python scripts/tao_staging.py --repeat 3          # raw -> staging, đo 3 lần
../.venv/Scripts/python scripts/tao_scales.py                       # tạo mức 10K/100K/500K
../.venv/Scripts/python scripts/chay_baseline.py --scales 10k 100k full --repeat 3
../.venv/Scripts/python scripts/kiem_tra_loi_doc.py
../.venv/Scripts/python scripts/tong_hop_w3.py                      # bảng + biểu đồ
```

Chốt chặn bộ nhớ: `runlog.Monitor` dừng lần chạy nếu tổng RSS > 3,5 GB hoặc RAM trống của máy < 3 GB.

Ghi chú: `results/raw/runs_baseline_lan1_bi_nhieu_RAM.jsonl` là lần chạy đầu, trùng thời điểm máy thiếu RAM do tiến trình khác (extension IDE lập chỉ mục thư mục dữ liệu). Không dùng trong bảng tổng hợp; giữ lại để minh bạch.
