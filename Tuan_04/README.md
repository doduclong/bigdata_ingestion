# Tuần 4 — Spark ETL v0.1, kiểm thử lược đồ, tỷ lệ lỗi

**Nhiệm vụ:** Cài Spark ETL; chuẩn hóa text, LaTeX, Lean và metadata; thêm test.
**Minh chứng:** Pipeline Spark v0.1; kiểm thử lược đồ; báo cáo tỷ lệ lỗi (+ checkpoint report theo tiến độ chung).

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần (checkpoint report) | `BaoCao_Tuan04.md` / `.docx` |
| Pipeline Spark | `src/mdl/spark_etl.py`, `scripts/chay_spark.py` |
| Kiểm thử (15 test) | `tests/`, kết quả `results/raw/pytest_w4.txt` |
| Parity Spark ↔ baseline trên toàn bộ 982K bản ghi | `scripts/kiem_tra_parity_full.py`, `results/raw/parity_full.json` |
| Kiểm tra bộ tách phát biểu Lean | `scripts/kiem_tra_formal_statement.py`, `results/raw/formal_statement_check.json` |
| Raw results | `results/raw/runs_spark.jsonl`, `results/raw/runs_baseline.jsonl` (+ các bản `_v0.2`, `_v0.3rc` để đối chiếu) |
| Bảng + biểu đồ | `results/tables/*.csv`, `results/figures/w4_*.png` |

## Lệnh tái tạo

```
cd Tuan_04
../.venv/Scripts/python -m pytest -q tests                           # dùng data_sample/, ~1 phút
../.venv/Scripts/python scripts/chay_baseline.py --scales 10k 100k full --repeat 3
../.venv/Scripts/python scripts/chay_spark.py --scales 10k 100k full --repeat 3 --cores 4
../.venv/Scripts/python scripts/kiem_tra_parity_full.py
../.venv/Scripts/python scripts/kiem_tra_formal_statement.py
../.venv/Scripts/python scripts/tong_hop_w4.py
```

Yêu cầu: staging và các mức quy mô đã tạo ở tuần 3 (`scripts/tao_staging.py`, `scripts/tao_scales.py`).
Giới hạn tài nguyên: Spark `local[4]`, driver 2 GB; mọi lần chạy bị chặn nếu tổng RSS > 3,5 GB.
