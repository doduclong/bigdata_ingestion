# 5. Bộ truy vấn kiểm tra

| Tệp | Nội dung |
|---|---|
| `truy_van_kiem_tra.sql` | Q0–Q5 (quét toàn bộ, đếm theo nguồn/split, lọc có tỉa partition, tra 20 ID, top premise, kiểm provenance) + 5 truy vấn ví dụ cho các nhóm khác |
| `chay_truy_van.py` | Chạy Q0–Q5 bằng DuckDB và **so với kết quả mong đợi**, in KHỚP/KHÁC |
| `ket_qua_mong_doi_mau.json` | Kết quả đúng trên kho mẫu (mục 1) |
| `ket_qua_mong_doi_full.json` | Kết quả đúng trên kho đầy đủ 982.477 bản ghi — đã đối chiếu khớp 6/6 với baseline Python quét JSONL (đường tính độc lập, tuần 8) |
| `query_ids.json` | 20 `record_id` dùng cho Q3 (18 có thật, 2 không tồn tại) |

```
python chay_truy_van.py                                                    # kho mẫu
python chay_truy_van.py --kho <storage>/lake/math_record --mong-doi ket_qua_mong_doi_full.json
```

Thời gian trên kho đầy đủ (DuckDB 4 luồng): tổng Q0–Q5 khoảng 0,7 s (DuckDB trên JSONL: 6,6 s; Python quét: 52 s).
