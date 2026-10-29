# API dữ liệu Math Data Lake — hướng dẫn cho Nhóm 2–8

Khởi động (máy có kho): `python scripts/mdl.py serve --port 8000` → tài liệu tương tác OpenAPI tại `http://localhost:8000/docs`.
Không có kho đầy đủ? Dùng mock input `data_sample/curated/math_record_sample.parquet` (cùng lược đồ, cùng `record_id`).

## Endpoint

| Phương thức | Đường dẫn | Tham số | Trả về | Nhóm dùng |
|---|---|---|---|---|
| POST | `/records` | JSON bản ghi theo nguồn, khóa, phiên bản và thông tin giấy phép | 201: thêm mới; 200: không đổi; 409: xung đột; 422: đầu vào sai | nạp gia tăng |
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

## Thêm dữ liệu thật vào kho đang phục vụ

POST `/records` dùng chính `MDL_LAKE` của server (mặc định `<storage>/lake`), không ghi vào kho demo riêng.
Cần Java 17/21 và cấu hình Hadoop Windows giống khi chạy Spark ETL. Server hiện chạy một worker;
chỉ chạy một tiến trình ghi vào kho, không chạy CLI ingest/ETL đồng thời với API ghi.

Luồng: kiểm tra JSON → raw bất biến → manifest → staging riêng → Spark ETL → append Parquet → `_lake_log`.
Các yêu cầu ghi được thực hiện tuần tự; không compaction tự động trong POST để các truy vấn đang đọc không mất tệp.
View DuckDB và cache catalog được làm mới sau mỗi yêu cầu ghi.

Chạy từ `Tuan_10/math_data_lake`, terminal thứ nhất:

```powershell
python scripts/mdl.py serve --host 0.0.0.0 --port 8000
```

Terminal thứ hai, cùng thư mục:

```powershell
curl.exe -i -X POST "http://localhost:8000/records" -H "Content-Type: application/json" --data-binary "@data_sample/api_record_test.json"
```

File mẫu gửi `problem: "test"`, `solution: "test"`, `source_record_key: "api-test-001"`,
`source_version: "api-v1"`, `license: "CC0-1.0"` và URL minh họa do người gửi khai báo.
`source: "numinamath"` chọn cách ánh xạ dữ liệu; không có nghĩa bản ghi tự nhập thuộc snapshot NuminaMath gốc.
Hãy dùng phiên bản `api-*` cho dữ liệu tự nhập và khai báo giấy phép/URL đúng với nguồn của bạn.
Không cần gửi 37 trường curated: pipeline tự tạo ID, checksum, cờ chất lượng và metadata xử lý.

Kết quả lần đầu: HTTP 201, JSON có `status: "created"`, `record_id`, `source_version`, `run_id`, `raw_uri`, `new: 1`.
Gửi lại cùng khóa/phiên bản và cùng `content_sha256`: HTTP 200, `status: "unchanged"`, không thêm tệp.
Giống quy tắc `lake.py`, checksum nội dung bao gồm đề bài, lời giải, phát biểu và chứng minh;
thay đổi riêng metadata không cập nhật bản ghi đã tồn tại. Muốn tạo phiên bản dữ liệu mới, đổi `source_version`.
Nếu cùng khóa/phiên bản mà checksum nội dung khác, API trả 409 và không ghi đè bản cũ.

Dùng `record_id` được trả về để đọc và truy vết (thay `<record_id>`):

```powershell
curl.exe "http://localhost:8000/records/<record_id>?source_version=api-v1"
curl.exe "http://localhost:8000/provenance/<record_id>?source_version=api-v1"
curl.exe "http://localhost:8000/health"
curl.exe "http://localhost:8000/catalog"
```

Nếu một ID có nhiều phiên bản, hai endpoint đọc chi tiết/truy vết yêu cầu `source_version` (nếu thiếu trả 409).
`GET /records` hiện vẫn phân trang theo `record_id`; khi cần xuất đầy đủ nhiều phiên bản, dùng `/export`.

Ngoài NuminaMath, schema POST hỗ trợ:

- ProofNet: `source: "proofnet"`, `source_record_key` bằng `data.id`, `split: "valid"` hoặc `"test"`;
  `data` gồm `id`, `nl_statement`, `formal_statement`, tùy chọn `nl_proof`, `src_header`.
- LeanDojo: `source: "leandojo"`, `source_record_key` bằng `file_path::full_name`;
  `data` gồm `file_path`, `full_name`, `start_line`, `end_line`, `code`;
  tùy chọn `imports` và `tactics` (mỗi tactic có `tactic`, `state_before`, `state_after`, `premises`).
  `code` là khai báo Lean để tách phát biểu; API không biên dịch hay xác minh chứng minh Lean.

Đầu ra sau khi thêm mới:

| Dữ liệu | Vị trí |
|---|---|
| Raw và metadata yêu cầu gốc | `<raw_root>/raw/api/<source>/<source_version>/<run_id>.jsonl` |
| Manifest bổ sung checksum/giấy phép | File `MDL_MANIFEST` (mặc định `manifest/manifest_full.json`) |
| Staging của yêu cầu | `<lake>/_api_batches/<run_id>/` |
| Bản ghi curated | `<lake>/math_record/source=<source>/source_version=<version>/*.parquet` |
| Lịch sử nạp | `<lake>/_lake_log/*.json` |

POST đợi Spark ghi xong mới trả kết quả, nên có thể mất vài chục giây. Nếu Spark lỗi, API trả 500;
raw/manifest/batch đã lưu vẫn được giữ để kiểm tra và gửi lại. Đây không phải giao dịch ACID nhiều tệp.
Các lần tạo lại manifest/staging từ raw cũng giữ các submission API để dựng lại kho.
API hiện chưa có xác thực: khi bind `0.0.0.0`, các máy kết nối được tới cổng 8000 cũng có thể gửi POST.

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
