# 2. Lược đồ + data dictionary

| Tệp | Nội dung |
|---|---|
| `data_dictionary.md` / `.csv` / `.docx` | 37 cột: nhóm, kiểu, null, miền giá trị, mô tả, tỷ lệ null theo nguồn (đo trên kho đầy đủ 982.477 bản ghi), ví dụ thật; bảng ánh xạ trường nguồn → cột chung |
| `data_contract.md` / `.docx` | Data contract v1.0: cam kết, danh sách cột, mã lỗi E01–E07, cờ W01–W06, cột từng nhóm dùng, quản lý phiên bản |
| `data_contract_v1.0.yaml` | Bản máy đọc của contract (sinh từ `mdl/schema.py`) |
| `tao_data_dictionary.py` | Sinh lại data dictionary: `python tao_data_dictionary.py` |

Nguồn sự thật duy nhất của lược đồ là `3_Pipeline_Ingest_ETL/src/mdl/schema.py`; contract và dictionary được sinh từ đó nên không lệch với mã.
