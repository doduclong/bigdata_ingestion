# Tuần 8 — Ablation, điểm nghẽn, phân tích lỗi

**Nhiệm vụ:** Ablation: JSONL/Parquet, có/không partition, nhiều tệp nhỏ/tệp hợp lý.
**Minh chứng:** Bảng ablation; phân tích điểm nghẽn và trường hợp lỗi (+ taxonomy lỗi, limitations).

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần | `BaoCao_Tuan08.md` / `.docx` |
| Ablation lưu trữ (3 lần) | `scripts/chay_luu_tru.py`, `results/raw/runs_storage_x3.jsonl`, `results/tables/storage_ablation_x3.csv` |
| Ablation Spark ETL + phân rã giai đoạn | `scripts/chay_ablation.py`, `results/raw/runs_ablation.jsonl`, `results/tables/ablation.csv`, `results/tables/stage_breakdown.csv` |
| Phân tích lỗi | `scripts/phan_tich_loi.py`, `results/tables/error_taxonomy.csv`, `results/raw/error_analysis.json` |
| Biểu đồ | `results/figures/w8_ablation.png`, `w8_stage_breakdown.png` |

## Lệnh tái tạo

```
cd Tuan_08
../.venv/Scripts/python scripts/chay_ablation.py --repeat 3
for i in 1 2 3: ../.venv/Scripts/python scripts/chay_luu_tru.py --repeat 1 --runs results/raw/runs_storage_x3.jsonl
../.venv/Scripts/python scripts/phan_tich_loi.py          # cần kho tuần 6 (_storage/lake_w6)
../.venv/Scripts/python scripts/tong_hop_w8.py
../.venv/Scripts/python scripts/tong_hop_luu_tru_x3.py
```
