# Bộ câu hỏi chuẩn bị bảo vệ cá nhân

Mỗi thành viên phải trả lời được phần **chung** và phần **vai trò của mình** (kèm số liệu và tệp minh chứng).

## A. Câu hỏi chung (mọi thành viên)

| Câu hỏi | Ý chính để trả lời | Minh chứng |
|---|---|---|
| Nút thắt Big Data của đề tài là gì? | đa dạng 3 nguồn/định dạng/biểu diễn; mảng JSON 373 MB phải nạp trọn; chi phí đọc–ghi; tệp nhỏ; cập nhật gia tăng | báo cáo §1 |
| Vì sao baseline là JSONL + Python tuần tự? | yêu cầu bắt buộc; cùng dữ liệu/máy/timeout; là mốc tối thiểu chạy end-to-end | `baseline.py`, tuần 3 |
| `record_id` tạo thế nào, vì sao ổn định? | sha1(source + "|" + khóa nguồn)[:20]; khóa chính kèm `source_version` | `transform.record_id` |
| Làm sao chứng minh "không mất provenance"? | 9 cột provenance 100%; truy vết 30/30 về đúng dòng raw, kiểm sha256 và nội dung | `results/raw/tuan_06/provenance_trace.json` |
| Spark có nhanh hơn không? | chỉ ở 982K và 4 nhân: 53,8 s so với 65,8 s; 10K chậm hơn ×11; 8 nhân chậm hơn 4 nhân vì heap 2 GB | `results/tables/t_quy_mo.csv` |
| Lợi ích chắc chắn nhất? | Parquet: dung lượng ÷5,2, truy vấn ×10,8 (cùng DuckDB), ×85 so với Python quét | `t_luu_tru.csv` |
| Số liệu có tái lập được không? | 3 lần lặp, median, min–max; raw results theo Phụ lục B; hình sinh bằng `tao_hinh_bao_cao.py` | `results/raw/` |
| Giới hạn lớn nhất? | một máy, RAM 4 GB, không ACID, phân loại lỗi bằng quy tắc | báo cáo §7 |

## B. Theo vai trò

**TV1 — contract/API**
- Thay đổi nào là "major"? (đổi tên/xóa/đổi kiểu cột → 2.0, báo trước 1 tuần).
- Vì sao phân trang theo khóa (`after`) thay vì offset? (ổn định, không quét lại phần đầu).
- API chống SQL injection thế nào? (kiểm miền giá trị, regex `record_id`, tham số SQL, danh sách cột hợp lệ).

**TV2 — NuminaMath**
- NuminaMath không có ID: khóa là gì, rủi ro gì khi nguồn phát hành lại? (`split:shard:row`; đối chiếu bằng `content_sha256`).
- Vì sao W05 không dùng để lọc? (≥ 95% ký hiệu tiền tệ).

**TV3 — ProofNet**
- Vì sao cần `formal_language`? (ProofNet Lean 3, LeanDojo Lean 4 — không biên dịch lẫn được).
- 2 bản ghi thiếu chứng minh NL được xử lý thế nào? (cảnh báo W01, vẫn vào kho).

**TV4 — LeanDojo**
- Phát biểu Lean lấy từ đâu? (corpus, join `file_path + full_name`, 100%).
- Lỗi 3,99% là gì và sửa thế nào? (`:=` trong `@[to_additive (attr := simp)]`; regex nhóm nguyên tử cắt ở mức ngoặc 0; dùng chung cho Python và Java).
- Truy vết trong mảng JSON 373 MB mà không tốn RAM? (`iter_json_array` đọc theo chunk, `raw_decode`).

**TV5 — Spark**
- Vì sao không dùng UDF Python? (chạy trong JVM, tránh tuần tự hóa sang Python; parity kiểm từng cột).
- Kiểm tra trùng khóa tốn bao nhiêu và vì sao? (−30% khi tắt; phải quét lại staging 3,7 GB do không cache được trong 2 GB).
- Phân rã thời gian? (parse 4%, ánh xạ 39%, kiểm trùng 11%, ghi + nén 46%).

**TV6 — lưu trữ/benchmark**
- Small-file problem đo được ra sao? (512 tệp → truy vấn +53%, Q1 ×9; compaction 28,5 s khôi phục).
- Vì sao row group 16 MB? (1 row group/tệp ⇒ partition LeanDojo đọc 1 luồng; 16 MB ⇒ Q4 nhanh ×2,8).
- Bytes I/O đo thế nào, hạn chế gì? (bộ đếm I/O hệ điều hành, gồm cả shuffle và thư viện JVM).

**TV7 — QA/kho**
- Idempotent được đảm bảo thế nào? (anti-join theo `record_id` + so `content_sha256`; nạp lại ⇒ 0 bản ghi mới).
- Nội dung đổi trong cùng phiên bản? (từ chối, E07, kho không đổi — test `test_content_conflict_is_quarantined`).
- Tiêm lỗi kiểm tra những gì? (8 loại: JSON cụt, sai UTF-8, không phải object, nội dung rỗng, nguồn lạ, trùng khóa, raw không có trong manifest, ProofNet thiếu formal).
