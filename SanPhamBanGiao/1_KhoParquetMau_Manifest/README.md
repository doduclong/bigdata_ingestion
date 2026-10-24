# 1. Kho Parquet mẫu và manifest

| Tệp | Nội dung |
|---|---|
| `kho_mau/math_record/source=*/source_version=*/*.parquet` | Kho mẫu 997 bản ghi (NuminaMath 497, ProofNet 200, LeanDojo 300), đúng bố cục kho thật: Parquet zstd, partition `source/source_version`, row group 16 MB, sắp xếp theo `record_id` |
| `kho_mau/_lake_log/00000{0,1,2}.json` | Nhật ký nạp: v0 nạp ban đầu (520 mới) → v1 batch mới (477 mới) → v2 nạp lại (0 mới, 477 không đổi) |
| `manifest/manifest_full.json`, `manifest_full.sha256` | Manifest snapshot đầy đủ: 19 tệp raw, 2,14 GB, sha256, phiên bản, giấy phép, ngày tải |
| `manifest/manifest_sample.json`, `checksums.sha256` | Manifest bản mẫu (sha256 tệp gốc + `sample_sha256` của tệp mẫu) |

Bản ghi mẫu có cùng `record_id` và provenance với kho đầy đủ. Kho đầy đủ (982.477 bản ghi, 441 MB) nằm ngoài Git; dựng lại bằng các lệnh `download`, `staging`, `etl` ở mục 3.

Truy vấn thử:

```
cd ../3_Pipeline_Ingest_ETL
python scripts/mdl.py --lake ../1_KhoParquetMau_Manifest/kho_mau query "SELECT source, split, count(*) FROM math_record GROUP BY ALL ORDER BY ALL"
```
