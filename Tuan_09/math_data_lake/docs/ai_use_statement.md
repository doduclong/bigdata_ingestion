# Tuyên bố sử dụng AI (AI-use statement)

Theo yêu cầu học phần, nhóm khai báo việc sử dụng công cụ AI:

| Hạng mục | Công cụ | Phần được hỗ trợ | Cách nhóm kiểm chứng |
|---|---|---|---|
| Mã nguồn | Claude (Anthropic) qua Claude Code | khung mã các module `mdl.*`, script thí nghiệm, test | chạy toàn bộ 20 test; test parity Spark ↔ Python trên từng cột; parity toàn bộ 982K bản ghi; tiêm lỗi 8 loại |
| Tài liệu | Claude | bản nháp báo cáo tuần, data card, data contract | mọi số liệu trong tài liệu được đối chiếu với tệp kết quả thô trong `results/raw/` |
| Phân tích lỗi | Claude | đề xuất quy tắc regex phân loại cờ chất lượng | kiểm tra bằng mắt các ví dụ; đã bác bỏ một giả thuyết sai (W04 do `\f`rac) sau khi xem ví dụ |

**Cam kết:**

1. Không có số liệu nào được nhập tay hoặc do AI "ước lượng": mọi bảng/biểu đồ sinh bằng script từ raw results.
2. Các sai sót do AI gây ra và đã được phát hiện, sửa: (a) heuristic tách phát biểu Lean cắt sai 3,99% định lý (phát hiện bằng kiểm tra cân bằng ngoặc, sửa ở v0.3); (b) đọc tệp ở chế độ văn bản làm một byte sai UTF-8 dừng cả tệp (phát hiện bằng tiêm lỗi); (c) nhận định ban đầu sai về nguyên nhân trùng nội dung LeanDojo và ký tự điều khiển (đã sửa sau khi xem dữ liệu).
3. Mỗi thành viên phải giải thích được phần mình phụ trách và toàn bộ pipeline khi bảo vệ; mã do AI hỗ trợ được nhóm đọc, chạy và chịu trách nhiệm.

*Nhóm điền thêm: tên thành viên đã dùng AI cho phần nào, prompt chính (nếu giảng viên yêu cầu).*
