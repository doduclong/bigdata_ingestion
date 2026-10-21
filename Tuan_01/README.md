# Tuần 1 — Khảo sát nguồn, chốt câu hỏi và lược đồ nháp

**Nhiệm vụ (theo hướng dẫn):** Khảo sát nguồn, giấy phép, trường dữ liệu; chốt câu hỏi và lược đồ bản nháp.
**Minh chứng cần nộp:** Đề cương 1 trang; danh mục nguồn; sơ đồ lược đồ v0.1 (+ board nhiệm vụ theo tiến độ chung).

| Minh chứng | Tệp |
|---|---|
| Đề cương 1 trang (mẫu Phụ lục A) | `DeCuong_1trang.md` / `DeCuong_1trang.docx` |
| Danh mục nguồn (số liệu thật) | `DanhMucNguon.md` / `.docx`, số thô `ket_qua/khao_sat_nguon.json` |
| Sơ đồ lược đồ v0.1 + kiến trúc nháp | `LuocDo_v0.1.md` / `.docx`, `hinh/*.png` |
| Board nhiệm vụ, phân vai | `BoardNhiemVu.md`, `board_nhiem_vu.csv` |
| Script tái tạo | `scripts/khao_sat_nguon.py`, `scripts/ve_so_do.py` |

## Tái tạo

Dữ liệu raw được tải vào `../_storage/raw` (không đưa vào thư mục nộp; script tải hoàn chỉnh có ở Tuần 2).

```
cd Tuan_01
../.venv/Scripts/python scripts/khao_sat_nguon.py --raw ../_storage/raw --out ket_qua/khao_sat_nguon.json
../.venv/Scripts/python scripts/ve_so_do.py
```

Máy khảo sát: Intel i7-12700 (12 nhân/20 luồng), 23,8 GB RAM, Windows 11, Python 3.11.0, Java 21.0.8. Thời gian chạy khảo sát được ghi trong trường `elapsed_s` của JSON.
