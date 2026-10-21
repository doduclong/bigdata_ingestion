# Tuần 6 — Provenance, catalog, cập nhật gia tăng

**Nhiệm vụ:** Bổ sung provenance, catalog và cơ chế cập nhật gia tăng.
**Minh chứng:** Data card; catalog; thử nghiệm thêm một batch dữ liệu mới.

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần | `BaoCao_Tuan06.md` / `.docx` |
| Data card v0.2 | `DataCard_v0.2.md` / `.docx` |
| Catalog (sinh tự động) | `catalog/catalog.md`, `catalog/catalog.json` |
| Cập nhật gia tăng + nhật ký kho | `src/mdl/lake.py`, `src/mdl/storage.py` (minor compaction) |
| Truy vết provenance | `src/mdl/provenance.py`, `results/raw/provenance_trace.json` |
| Thí nghiệm batch mới | `scripts/chay_gia_tang.py`, `results/raw/runs_incremental.jsonl`, `results/tables/incremental.csv`, `results/figures/w6_incremental.png` |
| Test (20) | `tests/` (thêm `test_lake.py`) |

## Lệnh tái tạo

```
cd Tuan_06
../.venv/Scripts/python -m pytest -q tests
../.venv/Scripts/python scripts/chay_gia_tang.py --repeat 3   # cần staging đầy đủ (tuần 3)
../.venv/Scripts/python scripts/tao_catalog.py
../.venv/Scripts/python scripts/tong_hop_w6.py
```
