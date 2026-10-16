# Tuần 9 — Release candidate, báo cáo dạng bài báo ngắn, demo script

**Nhiệm vụ:** Đóng gói kho mẫu, mã, truy vấn và báo cáo dạng bài báo ngắn.
**Minh chứng:** Release candidate; README; bản báo cáo; demo script.

| Minh chứng | Tệp |
|---|---|
| Release candidate 1.0.0-rc1 (cấu trúc theo mục 4 hướng dẫn) | `math_data_lake/` |
| README (mục tiêu, kiến trúc, cài đặt, dữ liệu, lệnh nhanh, tái tạo) | `math_data_lake/README.md` |
| Báo cáo dạng bài báo ngắn (8 trang) | `math_data_lake/report/BaoCao_BTL_Nhom1.{md,docx,pdf}` |
| Demo script + kịch bản trình diễn | `math_data_lake/scripts/demo.py`, `math_data_lake/docs/kich_ban_demo.md`, đầu ra mẫu `demo_output.txt` |
| Kho mẫu + truy vấn | `math_data_lake/data_sample/`, `src/mdl/sql_queries.py`, `docs/catalog/` |
| Tài liệu | `math_data_lake/docs/` (data card v1.0, system card, data contract v1.0, AI-use, privacy/license) |
| Raw results tuần 3–8 + hình sinh bằng script | `math_data_lake/results/` (`scripts/tao_hinh_bao_cao.py`) |

## Kiểm tra trước khi phát hành

- `python -m pytest -q tests` → 20 passed.
- `python scripts/mdl.py sample` → tái tạo 997 bản ghi curated bằng một lệnh, 0 lỗi.
- `python scripts/demo.py` → chạy hết trong ~31 s.
- `python scripts/tao_hinh_bao_cao.py` → sinh lại toàn bộ hình/bảng từ raw results.
