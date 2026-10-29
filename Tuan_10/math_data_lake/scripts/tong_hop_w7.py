"""Tuần 7: CSV kết quả thô (mỗi dòng một lần chạy) + bảng median/min/max + biểu đồ theo quy mô.

Chạy: python scripts/tong_hop_w7.py
"""
import csv
from pathlib import Path

import _path  # noqa: F401
from mdl.report import SCALE_N, load_runs, plot_scale, summarize, write_csv

runs = load_runs("results/raw/runs_baseline.jsonl", "results/raw/runs_spark.jsonl")
for r in runs:
    p, m = r["parameters"], r["metrics"]
    p["method"] = f"Spark {p['workers']} nhân" if r["experiment"] == "spark_etl" else "Baseline Python 1 nhân"
    if m.get("runtime_s"):
        m["throughput_e2e"] = round(m["records_in"] / m["runtime_s"], 1)
        m["read_mb"] = round(m["read_bytes"] / 2**20, 1)
        m["write_mb"] = round(m["write_bytes"] / 2**20, 1)
        m["out_mb"] = round(m["bytes_out"] / 2**20, 2)

# 1) CSV thô: mọi lần chạy, kể cả thất bại
cols = ["run_id", "timestamp", "experiment", "method", "scale", "repeat_idx", "workers", "status", "git_commit",
        "data_version", "runtime_s", "elapsed_s", "throughput_e2e", "peak_rss_mb", "read_mb", "write_mb", "out_mb",
        "files_out", "records_in", "records_out", "records_error", "schema_error_rate", "query_total_s",
        "sql_total_s", "log"]
Path("results/raw").mkdir(parents=True, exist_ok=True)
with open("results/raw/w7_all_runs.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in runs:
        p, m = r["parameters"], r["metrics"]
        w.writerow({"run_id": r["run_id"], "timestamp": r["timestamp"], "experiment": r["experiment"],
                    "method": p["method"], "scale": p["scale"], "repeat_idx": p["repeat_idx"],
                    "workers": p.get("workers"), "status": r["status"], "git_commit": r["git_commit"],
                    "data_version": r["data_version"], "log": r["log"], **{k: m.get(k) for k in cols[10:-1]}})

# 2) Bảng median/min/max
metrics = ["runtime_s", "throughput_e2e", "peak_rss_mb", "read_mb", "write_mb", "out_mb", "files_out",
           "records_out", "query_total_s", "sql_total_s", "schema_error_rate"]
rows = sorted(summarize(runs, ["method", "scale"], metrics), key=lambda r: (r["method"], SCALE_N[r["scale"]]))
write_csv(rows, "results/tables/w7_scale_summary.csv")

# 3) Biểu đồ
F = "results/figures/"
plot_scale(rows, "runtime_s", "Runtime end-to-end (s)", F + "w7_runtime.png", series_key="method", logx=False, show_values=True)
plot_scale(rows, "throughput_e2e", "Throughput (bản ghi/s)", F + "w7_throughput.png", series_key="method", logx=False, show_values=True)
plot_scale(rows, "peak_rss_mb", "Peak RSS (MB)", F + "w7_peak_rss.png", series_key="method", logx=False, show_values=True)
plot_scale(rows, "read_mb", "Bytes đọc (MB)", F + "w7_read_mb.png", series_key="method", logx=False, show_values=True)
plot_scale(rows, "write_mb", "Bytes ghi (MB)", F + "w7_write_mb.png", series_key="method", logx=False, show_values=True)

# Truy vấn: Python quét JSONL / DuckDB trên JSONL / DuckDB trên Parquet (Spark 4 nhân)
qrows = []
for r in rows:
    if r["method"].startswith("Baseline"):
        qrows.append({**r, "engine": "Python quét JSONL", "q_median": r["query_total_s_median"],
                      "q_min": r["query_total_s_min"], "q_max": r["query_total_s_max"]})
        qrows.append({**r, "engine": "DuckDB trên JSONL", "q_median": r["sql_total_s_median"],
                      "q_min": r["sql_total_s_min"], "q_max": r["sql_total_s_max"]})
    elif r["method"] == "Spark 4 nhân":
        qrows.append({**r, "engine": "DuckDB trên Parquet", "q_median": r["sql_total_s_median"],
                      "q_min": r["sql_total_s_min"], "q_max": r["sql_total_s_max"]})
plot_scale(qrows, "q", "Thời gian bộ truy vấn kiểm tra (s)", F + "w7_query.png", series_key="engine", logx=False, show_values=True)

# Hiệu suất song song của Spark ở mức toàn bộ
full = {r["method"]: r for r in rows if r["scale"] == "full"}
base = full["Baseline Python 1 nhân"]["runtime_s_median"]
speed = []
for k, r in full.items():
    speed.append({"method": k, "runtime_median_s": r["runtime_s_median"],
                  "speedup_vs_baseline": round(base / r["runtime_s_median"], 2)})
write_csv(speed, "results/tables/w7_speedup_full.csv")
for r in rows:
    print(r["method"], r["scale"], r["n_runs"], r["runtime_s_median"], r["throughput_e2e_median"],
          r["peak_rss_mb_max"], r.get("query_total_s_median"), r.get("sql_total_s_median"))
print(speed)
