# API dữ liệu Math Data Lake — hướng dẫn cho Nhóm 2–8

Khởi động (máy có kho): `python scripts/mdl.py serve --port 8000` → tài liệu tương tác OpenAPI tại `http://localhost:8000/docs`.
Không có kho đầy đủ? Dùng mock input `data_sample/curated/math_record_sample.parquet` (cùng lược đồ, cùng `record_id`).

## Endpoint

| Phương thức | Đường dẫn | Tham số | Trả về | Nhóm dùng |
|---|---|---|---|---|
| GET | `/health` | — | số bản ghi, phiên bản lược đồ/pipeline | tất cả |
| GET | `/stats` | — | số bản ghi theo nguồn/phiên bản/split | tất cả |
| GET | `/records/{record_id}` | `record_id` 20 ký tự hex | một bản ghi đầy đủ 37 cột | tất cả |
| GET | `/records` | `source`, `split`, `subset`, `has_lean`, `record_type`, `fields`, `limit` ≤ 1000, `after` | trang bản ghi + `next_after` (phân trang theo khóa) | 2, 5, 8 |
| GET | `/premises/{premise}/theorems` | `limit` | định lý LeanDojo dùng premise | 3, 4, 7 |
| GET | `/pairs/nl-formal` | `split` = valid/test | cặp NL – Lean 3 (ProofNet) | 5, 6 |
| GET | `/provenance/{record_id}` | — | tệp raw, dòng, sha256 hợp lệ?, các trường đối chiếu | 2, kiểm toán |
| GET | `/catalog` | — | catalog JSON (cột, partition, lịch sử nạp, chất lượng) | tất cả |
| GET | `/export` | `source` (bắt buộc), `split`, `fields`, `fmt` = parquet/jsonl | tệp tải về (ghi theo batch, RAM ổn định) | 2, 3, 4, 7 |

Bảo vệ đầu vào: `record_id` phải khớp `^[0-9a-f]{20}$`; `source`, `record_type`, `split` của ProofNet kiểm theo miền giá trị; `fields` chỉ nhận tên cột trong lược đồ; mọi giá trị truyền dạng tham số SQL.

## Client Python

```
from mdl.client import MathLakeClient
c = MathLakeClient("http://localhost:8000")
c.health()
pairs = c.nl_formal_pairs(split="test")                                   # Nhóm 5
for r in c.iter_records(source="numinamath", subset="olympiads",
                        fields="record_id,nl_problem,content_sha256"):    # Nhóm 2, 8
    ...
c.theorems_using("Nat.succ_le_iff")                                       # Nhóm 3, 4
c.export("leandojo", split="test", path="leandojo_test.parquet")          # Nhóm 3, 4, 7
c.provenance("00f6e184715f8cd8dbe9")
```

## Hiệu năng đo được (kho 982.477 bản ghi, 1 tiến trình uvicorn, DuckDB 4 luồng/1 GB)

Hỗn hợp truy vấn: 70% tra cứu `record_id`, 20% lọc theo nguồn/subset (50 bản ghi), 10% tra premise; 1.500 request mỗi mức; 3 lần.

| Client đồng thời | QPS median (min–max) | P50 ms | P95 ms | P99 ms | Lỗi | RSS server |
|---|---|---|---|---|---|---|
| 1 | 31,6 (30,3–34,0) | 28,5 | 57,1 | 62,2 | 0 | ≤ 480 MB |
| 10 | 85,0 (75,1–129,5) | 119,9 | 169,1 | 181,3 | 0 | ≤ 480 MB |
| 50 | 88,5 (79,9–103,9) | 569,1 | 772,9 | 880,7 | 0 | ≤ 483 MB |

Thông lượng bão hòa ở ~85–130 QPS từ 10 client; với 50 client độ trễ tăng do xếp hàng (một tiến trình). Thông lượng ở 10 client giảm qua 3 lần lặp (129,5 → 85,0 → 75,1) — chưa xác định nguyên nhân (nghi bộ đệm/điều tiết nhiệt), nên báo cáo median và khoảng.

**Hướng tối ưu khi cần tải lớn hơn:** nhiều worker uvicorn; bảng chỉ mục `record_id → tệp/row group` nạp sẵn vào RAM; cache kết quả lọc hay dùng.

## Hợp đồng

Lược đồ và bảo đảm: `docs/data_contract.md` (v1.0). Thay đổi phá vỡ tương thích được báo trước 1 tuần, giữ bản cũ song song.
