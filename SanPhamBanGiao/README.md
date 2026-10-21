# Sản phẩm bàn giao — Nhóm 1 Math Data Lake

Tổ chức đúng theo mục **10. Sản phẩm bàn giao** của đề bài Nhóm 1. Mỗi thư mục con có README riêng.

| # | Sản phẩm (theo đề bài) | Thư mục | Tệp chính |
|---|---|---|---|
| 1 | Kho Parquet mẫu và manifest | `1_KhoParquetMau_Manifest/` | `kho_mau/` (997 bản ghi, partition, `_lake_log`), `manifest/manifest_full.json` |
| 2 | Lược đồ + data dictionary | `2_LuocDo_DataDictionary/` | `data_dictionary.md/.csv`, `data_contract.md`, `data_contract_v1.0.yaml` |
| 3 | Pipeline ingest/ETL | `3_Pipeline_Ingest_ETL/` | `src/mdl/`, `scripts/mdl.py`, `tests/` (25 test) |
| 4 | Data card và license note | `4_DataCard_LicenseNote/` | `data_card.md`, `privacy_license_note.md`, `system_card.md` |
| 5 | Bộ truy vấn kiểm tra | `5_BoTruyVanKiemTra/` | `truy_van_kiem_tra.sql`, `chay_truy_van.py`, kết quả mong đợi |
| 6 | Raw results + biểu đồ | `6_RawResults_BieuDo/` | `raw/tuan_03…10/`, `figures/`, `tables/` |
| 7 | README và demo | `7_README_Demo/` | `README.md`, `demo.py`, `demo_output.txt`, kịch bản, slide, báo cáo |

## Đối chiếu tiêu chí nghiệm thu tối thiểu (mục 11)

| Tiêu chí | Minh chứng |
|---|---|
| Đọc được tối thiểu 3 nguồn | mục 3 `src/mdl/readers.py`; kho mẫu ở mục 1 có đủ 3 nguồn |
| Tái tạo được curated sample bằng một lệnh | `cd 3_Pipeline_Ingest_ETL` rồi `python scripts/mdl.py sample` |
| Có baseline và ít nhất 3 mức quy mô | mục 6 `raw/tuan_07/w7_all_runs.csv` (4 mức × 3 lần) |
| Không mất trường nguồn/giấy phép/phiên bản | mục 5 Q5 (provenance 100%); mục 6 `raw/tuan_06/provenance_trace.json` (30/30) |
| Một nhóm khác sử dụng được data contract | mục 2 contract v1.0 + mock input + API (`docs/api.md`); cần xác nhận của nhóm tiêu thụ |

Bản dự án đầy đủ, tổ chức theo cấu trúc chuẩn README/src/tests/docs/results: `../Tuan_10/math_data_lake/`.
