
#  Nhiệm vụ cần làm và hướng dẫn chạy kết quả

```pip
Chuẩn bị

conda create -n bigdata python=3.11 -y
conda activate bigdata
cd D:\PTIT\Bigdata\bigdata_ingestion\Tuan_10\math_data_lake
python -m pip install -r requirements.lock.tx


Cài Hadoop 3.4.1 và JDK 17 vào _storage 
Set env 
$env:JAVA_HOME = "$PWD\_storage\java17\jdk-17.0.20.1+1"
$env:HADOOP_HOME = "$PWD\_storage\hadoop"
$env:PATH = "$env:JAVA_HOME\bin;$env:HADOOP_HOME\bin;$env:PATH"
```

## Tuần 1

**Nhiệm vụ bắt buộc:** Khảo sát nguồn, giấy phép, trường dữ liệu; chốt câu hỏi và lược đồ bản nháp.

**Minh chứng cần nộp:** Đề cương 1 trang; danh mục nguồn; sơ đồ lược đồ v0.1.

**Hướng dẫn chạy và kết quả:**

```
Nguồn, giấy phép, trường dx liệu... được lấy theo Tuan_10\math_data_lake\src\mdl\config.py
```

```
python scripts/mdl.py download
Tải toàn bộ dữ liệu theo 3 nguồn, lưu tại Tuan_10\math_data_lake\_storage\raw
```

```
Lược đồ  nháp tại Tuan_10\math_data_lake\results\figures\so_do_luoc_do_v0.1.png
```

**Ghi chú:**

## Tuần 2

**Nhiệm vụ bắt buộc:** Tải snapshot nhỏ; xây manifest và data contract; tạo 100–1.000 bản ghi mẫu.

**Minh chứng cần nộp:** Raw sample; checksum; data contract; script đọc được cả ba nguồn.

**Hướng dẫn chạy và kết quả:**

```
python scripts/tao_mau.py 
Lấy một phần dữ liệu từ raw đầy đủ để tạo bộ mẫu nhỏ, giúp chạy thử và kiểm tra pipeline nhanh hơn.
Kết quả trong data_sample/:
- raw/: 997 bản ghi mẫu từ 3 nguồn.
- staging/: dữ liệu mẫu chuyển sang JSONL để xử lý.
- curated/: dữ liệu mẫu đã đưa về schema chung, lưu dạng JSONL và Parquet; kèm file lỗi.
- sample_summary.json: thống kê số bản ghi và lỗi.
```

```
Tuan_10\math_data_lake\docs\data_contract_v1.0.yaml 
data contract
```

```
python scripts/doc_thu_nguon.py
Đọc được số sample tại Tuan_10\math_data_lake\data_sample
numinamath 497 records 0.02 s
proofnet 200 records 0.0 s
leandojo 300 records 0.02 s
leandojo_corpus 567 records 0.0 s
```

## Tuần 3

**Nhiệm vụ bắt buộc:** Cài baseline JSONL + Python tuần tự; đo thời gian và dung lượng.

**Minh chứng cần nộp:** Baseline chạy end-to-end; raw timing; báo cáo lỗi đọc.

**Hướng dẫn chạy và kết quả:**

```
Pipe line tổng quan
Raw → staging JSONL → baseline Python → curated JSONL
                                      + file lỗi
                                      + số liệu thời gian, RAM, dung lượng
```

```
# Chuyển raw đầy đủ sang staging jsonl lưu tại -> Tuan_10/math_data_lake/_storage/staging/*.jsonl
python scripts/mdl.py staging 

# Chuẩn bị các mức dữ liệu cho thí nghiệm chia nguồn thành 3 mức dữ liệu 10k 100k 500k lưu tại Tuan_10\math_data_lake\_storage\staging_scales
python scripts/tao_scales.py

# Chạy baseline mức 10.000 bản ghi, lặp 3 lần lưu kết quả hiệu năng tại Tuan_10\math_data_lake\logs
python scripts/chay_baseline.py --scales 10k --repeat 3

Lưu ý: python scripts/chay_baseline.py --scales full --repeat 1 -> chạy toàn các cấu hình data
```

## Tuần 4

**Nhiệm vụ bắt buộc:** Cài Spark ETL; chuẩn hóa text, LaTeX, Lean và metadata; thêm test.

**Minh chứng cần nộp:** Pipeline Spark v0.1; kiểm thử lược đồ; báo cáo tỷ lệ lỗi.

**Hướng dẫn chạy và kết quả:**

```
python scripts/mdl.py etl
Chạy Spark ETL để dữ liệu theo parquet theo cấu trúc math_record, kết quả tại Tuan_10\math_data_lake\_storage\lake\math_record

Lưu ý; cần chạy tuần 3 trước
```

**Ghi chú:**

## Tuần 5

**Nhiệm vụ bắt buộc:** Thiết kế Parquet, partition và kích thước tệp; xử lý small-file problem.

**Minh chứng cần nộp:** Ba cấu hình lưu trữ; bảng số tệp, dung lượng, thời gian đọc.

**Hướng dẫn chạy và kết quả:**

6 cấu hình

| Cấu hình                                     | Giải thích đơn giản                                                                                                                                                |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L1 — Lưu chung**                     | Để cả ba nguồn trong một thư mục, chia thành các file có kích thước mục tiêu khoảng **128 MiB** .                                                 |
| **L2 — Chia theo nguồn**               | Tạo thư mục riêng cho từng **nguồn và phiên bản** , rồi chia file trong mỗi thư mục, mục tiêu khoảng **128 MiB/file** .                     |
| **L3 — Chia nhỏ theo nhóm nội dung** | Giống L2 nhưng chia thêm thư mục theo **`subset`** . Mỗi nhóm nguồn + phiên bản + subset được ghi thành một file.                                |
| **L4 — Tạo nhiều file nhỏ**          | Chia thư mục giống L2, nhưng mỗi file chứa **tối đa 2.000 hàng** . Dùng để thử ảnh hưởng của nhiều file nhỏ.                                   |
| **L5 — Gộp file nhỏ**                 | Lấy kết quả L4,**gộp các file nhỏ trong cùng thư mục**thành ít file lớn hơn, mục tiêu khoảng **128 MiB/file** .                             |
| **L6 — Chia khối bên trong file**     | Chia thư mục và file giống L2, nhưng bên trong file có các khối hàng ( **row group** ) mục tiêu **16 MiB/khối** . Không tạo thêm thư mục. |

```

# 1. Tạo baseline — bỏ qua nếu đã chạy thành công trên cùng dữ liệu
python scripts/chay_baseline.py --scales full --repeat 1

# 2. Tạo Parquet đầu vào — bỏ qua nếu đã chạy thành công trên cùng dữ liệu
python scripts/chay_spark.py --scales full --repeat 1 --cores 4

# 3. Tạo 6 cấu hình và đo truy vấn 3 lần/cấu hình dùng duck db để độc
python scripts/chay_luu_tru.py --repeat 3 --layouts L1_parquet_flat L2_parquet_src_ver L3_parquet_src_ver_subset L4_parquet_small_files L5_parquet_compacted L6_parquet_src_ver_rg16

# 4. Tổng hợp kết quả, lưu tại results/tables/storage_layouts.csv, results/figures/w5_layouts.png, w5_queries.png
python scripts/tong_hop_w5.py
```

```
Quy trình
Staging JSONL
    ↓ Bước 2: chay_spark.py
Parquet đã chuẩn hóa
    ↓ Bước 3: chay_luu_tru.py
6 bộ Parquet có cách chia file khác nhau
 ↓
 Chạy tong_hop_w5.py xuất kết quả (dùng )
```

# Tuần 6

**Nhiệm vụ bắt buộc:** Bổ sung provenance, catalog và cơ chế cập nhật gia tăng.

**Minh chứng cần nộp:** Data card; catalog; thử nghiệm thêm một batch dữ liệu mới.

**Hướng dẫn chạy và kết quả:**

```
Cơ chế cập nhật gia tăng 
Dựng kho đầy đủ làm mốc đối chiếu
        ↓
v0: Nạp ban đầu, trừ shard 4 của NuminaMath
        ↓
v1: Nạp shard 4 → thêm 171.898 bản ghi
        ↓
v2: Nạp lại shard 4 → thêm 0, bỏ qua 171.898 bản ghi không đổi
        ↓
So sánh kho gia tăng với kho dựng đầy đủ, nếu có đủ 982.477 bản ghi tức đã tái hiện thành coong


python scripts/chay_gia_tang.py --repeat 1

Kết quả 
Bước	Kết quả	Thời gian
Dựng lại toàn bộ	982.477 bản ghi hợp lệ	122,595 giây
v0 — Nạp ban đầu	Thêm 810.579 bản ghi	110,438 giây
v1 — Thêm shard 4	Thêm 171.898, không xung đột	45,140 giây
v2 — Nạp lại shard 4	Thêm 0, bỏ qua 171.898 bản ghi không đổi	37,698 giây

810.579 + 171.898 = 982.477 bản ghi
Cho thấy có thể thể nạp gia tăng số lượng lớn
```

```
Cơ chế tạo catalog: thống kê cấu trúc, số bản ghi, partition, chất lượng và lịch sử nạp của kho
Cơ chế rovenance: chọn 10 bản ghi mỗi nguồn, tổng 30 bản ghi, truy ngược về raw và kiểm tra tính khớp.

Kết quả
catalog/catalog.json: Catalog dạng JSON
catalog/catalog.md: Catalog dạng tài liệu dễ đọc 
results/raw/provenance_trace.json Chi tiết kiểm tra nguồn gốc 30 bản ghi
```

> ```
> Có api truy xuất nguồn gốc: http://localhost:8000/provenance/00027534e2249bc74d37
> ```

**Ghi chú:**

> Cần update api cho phép thêm reocord

```
```

## Tuần 7

**Nhiệm vụ bắt buộc:** Chạy 10K, 100K và toàn bộ dữ liệu; lặp ít nhất 3 lần.

**Minh chứng cần nộp:** CSV kết quả thô; biểu đồ runtime, throughput, RAM, bytes I/O.

**Hướng dẫn chạy và kết quả:**

```
                  ┌→ Python tuần tự → JSONL   → DuckDB
Staging .json  giống nhau┤
                  └→ Spark 4 nhân   → Parquet → DuckDB

# Baseline Python: 3 mức × 3 lần
python scripts/chay_baseline.py --scales 10k 100k full --repeat 3 --sql

# Spark 4 nhân: 3 mức × 3 lần
python scripts/chay_spark.py --scales 10k 100k full --repeat 3 --cores 4 --queries

# Tổng hợp kết quả 
python scripts/tong_hop_w7.py

# Kếtt quả
results/raw/runs_baseline.jsonl
results/raw/runs_spark.jsonl
figures/w7_runtime

Dữ liệu scale dùng: python scripts/tao_scales.py - 
 Tuan_10\math_data_lake\_storage\staging_scales;
```

**Ghi chú:**

## Tuần 8

**Nhiệm vụ bắt buộc:** Ablation: JSONL/Parquet, có/không partition, nhiều tệp nhỏ/tệp hợp lý.

**Minh chứng cần nộp:** Bảng ablation; phân tích điểm nghẽn và trường hợp lỗi.

**Hướng dẫn chạy và kết quả:**

```
Các thí nghiệm về ablation cơ bản là tuần 5 với các cấu hình parquet
```

```
python scripts/phan_tich_loi.py

results/raw/error_analysis.json: số lượng, ví dụ và phân bố theo subset.
results/tables/error_taxonomy.csv: bảng phân loại W04/W05, số lượng và tỷ lệ.

Nhóm	Nội dung
W05	Dấu $ không cân bằng: tiền tệ, dấu escape, $$…
W04	Ký tự điều khiển bất thường
W03	Ký tự thay thế �, dấu hiệu lỗi giải mã
E_errors	Danh sách lỗi cứng của pipeline
exact_duplicates	Các nhóm có cùng content_sha256
```

**Ghi chú:**

## Tuần 9

**Nhiệm vụ bắt buộc:** Đóng gói kho mẫu, mã, truy vấn và báo cáo dạng bài báo ngắn.

**Minh chứng cần nộp:** Release candidate; README; bản báo cáo; demo script.

**Hướng dẫn chạy và kết quả:**

**Ghi chú:**

## Tuần 10

**Nhiệm vụ bắt buộc:** Tích hợp API dữ liệu cho nhóm khác; demo và bảo vệ cá nhân.

**Minh chứng cần nộp:** Bản bàn giao cuối; video/demo; bảng đóng góp cá nhân.

**Hướng dẫn chạy và kết quả:**

```
python scripts/mdl.py serve --host 0.0.0.0 --port 8000
```

**Ghi chú:**

```Shell
Tạo dữ liệu
@'
{
  "source": "numinamath",
  "source_version": "api-v1",
  "source_record_key": "demo-addition-001",
  "license": "CC0-1.0",
  "source_url": "https://example.org/demo/addition-001",
  "split": "test",
  "data": {
    "source": "manual_demo",
    "problem": "Calculate 2 + 3.",
    "solution": "2 + 3 = 5."
  }
}
'@ | curl.exe -i -X POST "http://localhost:8000/records" -H "Content-Type: application/json" --data-binary "@-"
```

```
record id minh họa: 443275463784cdff3c17
```
