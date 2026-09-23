"""Sinh bảng và biểu đồ tuần 3 từ results/raw/runs_baseline.jsonl. Chạy: python scripts/tong_hop_w3.py"""
import _path  # noqa: F401
from mdl.report import SCALE_N, load_runs, plot_scale, summarize, write_csv

runs = load_runs("results/raw/runs_baseline.jsonl")
for r in runs:  # đưa thời gian từng truy vấn lên mức metric để tổng hợp
    for q, v in r["metrics"].get("queries", {}).items():
        r["metrics"][q] = v["seconds"]
metrics = ["runtime_s", "throughput_rps", "peak_rss_mb", "read_bytes", "write_bytes", "bytes_in", "bytes_out",
           "records_out", "schema_error_rate", "query_total_s", "Q1_count_by_source_split", "Q2_olympiad_latex",
           "Q3_point_lookup", "Q4_top_premises", "Q5_provenance_audit"]
rows = sorted(summarize(runs, ["scale"], metrics), key=lambda r: SCALE_N[r["scale"]])
write_csv(rows, "results/tables/baseline_summary.csv")
plot_scale(rows, "runtime_s", "Runtime ETL (s)", "results/figures/w3_runtime.png", logy=True)
plot_scale(rows, "throughput_rps", "Throughput (bản ghi/s)", "results/figures/w3_throughput.png")
plot_scale(rows, "peak_rss_mb", "Peak RSS (MB)", "results/figures/w3_peak_rss.png")
plot_scale(rows, "query_total_s", "Tổng thời gian 5 truy vấn (s)", "results/figures/w3_query.png", logy=True)
for r in rows:
    print({k: r[k] for k in r if k.endswith("_median") or k in ("scale", "n_runs")})
