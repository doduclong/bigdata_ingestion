# 3. Pipeline ingest/ETL

Mã nguồn đầy đủ, chạy được độc lập (README dự án: `README.md` ở mục 7).

| Giai đoạn | Mã | Lệnh |
|---|---|---|
| Tải + manifest + checksum | `src/mdl/manifest.py` | `python scripts/mdl.py download` · `verify` |
| Raw → staging (3 reader) | `src/mdl/readers.py`, `staging.py` | `python scripts/mdl.py staging` |
| Ánh xạ tham chiếu + kiểm lỗi | `src/mdl/transform.py`, `schema.py` | dùng bởi baseline và test parity |
| Baseline JSONL + Python | `src/mdl/baseline.py` | `python scripts/chay_baseline.py` |
| Spark ETL → Parquet | `src/mdl/spark_etl.py` | `python scripts/mdl.py etl` |
| Nạp gia tăng + compaction | `src/mdl/lake.py`, `storage.py` | `python scripts/mdl.py ingest <staging_batch>` |
| Catalog, provenance, API | `catalog.py`, `provenance.py`, `api.py`, `client.py` | `mdl.py catalog` · `trace <id>` · `serve` |
| Mẫu dữ liệu | `sample.py`, `data_sample/` | `python scripts/mdl.py sample` — tái tạo curated mẫu bằng một lệnh |
| Kiểm thử | `tests/` (25 test) | `python -m pytest -q tests` |

Môi trường: `requirements.lock.txt` (Python 3.11, PySpark 4.0.1, Java 21). Giới hạn RAM: mọi lần chạy ≤ 3,5 GB.
