# Tuần 2 — Snapshot, manifest, data contract, dữ liệu mẫu

**Nhiệm vụ:** Tải snapshot nhỏ; xây manifest và data contract; tạo 100–1.000 bản ghi mẫu.
**Minh chứng:** Raw sample; checksum; data contract; script đọc được cả ba nguồn (+ data sample và data card v0.1 theo tiến độ chung).

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần | `BaoCao_Tuan02.md` / `.docx` |
| Raw sample (997 bản ghi, cùng định dạng gốc) | `data_sample/raw/` |
| Checksum | `data_sample/checksums.sha256`, `manifest/manifest_full.sha256` |
| Manifest | `manifest/manifest_full.json`, `data_sample/manifest_sample.json` |
| Data contract | `DataContract_v0.1.md` / `.docx`, `contract/data_contract_v0.1.yaml` |
| Data card v0.1 | `DataCard_v0.1.md` / `.docx` |
| Mock input lược đồ chung | `data_sample/curated/math_record_sample.{parquet,jsonl}` |
| Script đọc 3 nguồn | `src/mdl/readers.py`, `scripts/doc_thu_nguon.py`, kết quả `ket_qua/doc_thu_*.json` |

## Mã nguồn (`src/mdl`)

| Module | Chức năng |
|---|---|
| `config.py` | đường dẫn kho, danh mục nguồn ghim phiên bản |
| `manifest.py` | tải, giải nén, sha256, manifest, verify |
| `readers.py` | đọc raw 3 nguồn → bản ghi staging (NFC, con trỏ raw) |
| `staging.py` | ghi staging JSONL; đọc JSONL có bắt lỗi parse; nạp bảng corpus |
| `schema.py` | lược đồ `math_record` v1.0 (nguồn duy nhất cho contract/Arrow/Spark) |
| `transform.py` | ánh xạ staging → lược đồ chung, cờ chất lượng, kiểm tra lỗi cứng |
| `sample.py` | chọn mẫu xác định bằng hash, giữ số dòng gốc |

## Lệnh tái tạo

```
cd Tuan_02
../.venv/Scripts/python scripts/tai_du_lieu.py            # tải + manifest (bỏ qua tệp đã có)
../.venv/Scripts/python scripts/tai_du_lieu.py --verify   # kiểm checksum
../.venv/Scripts/python scripts/tao_mau.py                # tạo data_sample/ (một lệnh)
../.venv/Scripts/python scripts/doc_thu_nguon.py --raw data_sample/raw
../.venv/Scripts/python scripts/xuat_data_contract.py
```

Dữ liệu đầy đủ nằm ở `../_storage/raw` (đổi bằng biến môi trường `MDL_STORAGE`).
