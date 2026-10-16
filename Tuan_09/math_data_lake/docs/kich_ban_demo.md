# Kịch bản demo (7 phút) — Math Data Lake

Chuẩn bị trước: đã cài môi trường; đã chạy `python scripts/mdl.py staging` và `python scripts/mdl.py etl` trên dữ liệu đầy đủ (kho `<storage>/lake`). Mở sẵn `docs/catalog/catalog.md` và `results/figures/`.

| Phút | Người trình bày | Nội dung | Lệnh / màn hình |
|---|---|---|---|
| 0:00–0:45 | TV1 | Bài toán: 3 nguồn, 3 định dạng, 3 biểu diễn; 2 câu hỏi nghiên cứu; nút thắt Big Data | slide 1–3 |
| 0:45–2:30 | TV7 | Demo end-to-end trên mẫu 997 bản ghi: staging → nạp v0/v1/v2 (idempotent) → catalog → truy vấn cho Nhóm 3/4/5/2 → truy vết provenance | `python scripts/demo.py` |
| 2:30–3:30 | TV5 | Kho đầy đủ: truy vấn trực tiếp ~1 triệu bản ghi trong < 1 s | `python scripts/mdl.py query "SELECT source, split, count(*) FROM math_record GROUP BY ALL ORDER BY ALL"` |
| 3:30–4:15 | TV4 | Truy vết một định lý LeanDojo về dòng trong `random/train.json` (đọc theo luồng, kiểm sha256) | `python scripts/mdl.py trace <record_id>` |
| 4:15–5:30 | TV6 | Kết quả quy mô: baseline và Spark, định dạng, tệp nhỏ, nạp gia tăng | `results/figures/h2_runtime.png`, `h4_truy_van.png`, `h5_luu_tru.png`, `h7_gia_tang.png` |
| 5:30–6:30 | TV2, TV3 | Phân tích lỗi: 5 bản ghi lỗi, ligature OT1, `$` tiền tệ; sửa tách phát biểu Lean 3,99% → 0,001% | `results/figures/h6_phan_ra.png`, bảng lỗi |
| 6:30–7:00 | TV1 | Giới hạn, bàn giao (data contract v1.0, mock input), hướng phát triển | slide cuối |

**Phương án dự phòng:** nếu Spark lỗi trên máy trình chiếu, chạy `python scripts/mdl.py sample` (Python thuần, không cần Spark) và mở `demo_output.txt` đã lưu.
