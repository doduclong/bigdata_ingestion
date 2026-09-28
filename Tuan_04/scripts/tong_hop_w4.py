"""Bảng + biểu đồ tuần 4: Spark ETL so với baseline (cùng mã pipeline v0.3, cùng máy, cùng dữ liệu)."""
import _path  # noqa: F401
from mdl.report import SCALE_N, load_runs, plot_scale, summarize, write_csv

runs = load_runs("results/raw/runs_baseline.jsonl", "results/raw/runs_spark.jsonl")
for r in runs:
    r["parameters"]["method"] = "Spark 4 nhân" if r["experiment"] == "spark_etl" else "Baseline Python 1 nhân"
    m = r["metrics"]
    if m.get("runtime_s"):
        m["throughput_e2e"] = round(m["records_in"] / m["runtime_s"], 1)  # end-to-end, gồm mọi chi phí
metrics = ["runtime_s", "elapsed_s", "throughput_e2e", "peak_rss_mb", "bytes_out", "files_out", "records_out",
           "records_error", "schema_error_rate"]
rows = sorted(summarize(runs, ["method", "scale"], metrics), key=lambda r: (r["method"], SCALE_N[r["scale"]]))
write_csv(rows, "results/tables/spark_vs_baseline.csv")
plot_scale(rows, "runtime_s", "Runtime end-to-end (s)", "results/figures/w4_runtime.png", series_key="method",
           logy=True)
plot_scale(rows, "throughput_e2e", "Throughput end-to-end (bản ghi/s)", "results/figures/w4_throughput.png",
           series_key="method")
plot_scale(rows, "peak_rss_mb", "Peak RSS (MB)", "results/figures/w4_peak_rss.png", series_key="method")
plot_scale(rows, "bytes_out", "Dung lượng đầu ra (byte)", "results/figures/w4_bytes_out.png", series_key="method",
           logy=True)
for r in rows:
    print(r["method"], r["scale"], r["runtime_s_median"], r["throughput_e2e_median"], r["peak_rss_mb_median"],
          r["bytes_out_median"], r.get("files_out_median"), r["records_error_median"])

# Chi phí của bộ tách formal_statement theo mức ngoặc (v0.3) so với cắt tại ':=' đầu tiên (v0.2), Spark mức full
old = [r for r in load_runs("results/raw/runs_spark_v0.2.jsonl") if r["parameters"]["scale"] == "full"]
new = [r for r in runs if r["experiment"] == "spark_etl" and r["parameters"]["scale"] == "full"]
for r in old:
    r["parameters"]["version"] = "v0.2 (cắt ':=' đầu tiên)"
for r in new:
    r["parameters"]["version"] = "v0.3 (cắt ':=' ở mức ngoặc 0)"
write_csv(summarize(old + new, ["version"], ["runtime_s", "elapsed_s", "peak_rss_mb"]),
          "results/tables/spark_v02_vs_v03.csv")
