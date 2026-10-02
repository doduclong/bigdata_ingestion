# Tuần 5 — Parquet, partition, kích thước tệp, small-file problem

**Nhiệm vụ:** Thiết kế Parquet, partition và kích thước tệp; xử lý small-file problem.
**Minh chứng:** Ba cấu hình lưu trữ; bảng số tệp, dung lượng, thời gian đọc (+ pipeline v0.2, test, environment lock theo tiến độ chung).

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần | `BaoCao_Tuan05.md` / `.docx` |
| Bố trí lưu trữ + compaction | `src/mdl/storage.py` |
| Bộ truy vấn SQL (DuckDB) | `src/mdl/sql_queries.py` |
| Script thí nghiệm | `scripts/chay_luu_tru.py`, `scripts/tong_hop_w5.py` |
| Raw results | `results/raw/runs_storage.jsonl`, log từng lần chạy trong `logs/` |
| Bảng + hình | `results/tables/storage_layouts.csv`, `results/figures/w5_layouts.png`, `w5_queries.png` |
| Test (17) | `tests/` (thêm `test_storage.py`) |
| Environment lock | `requirements.txt`, `requirements.lock.txt` |

## Lệnh tái tạo

```
cd Tuan_05
../.venv/Scripts/python -m pytest -q tests
../.venv/Scripts/python scripts/chay_luu_tru.py --repeat 3      # cần đầu ra full của tuần 4 trong _storage/out
../.venv/Scripts/python scripts/tong_hop_w5.py
```
