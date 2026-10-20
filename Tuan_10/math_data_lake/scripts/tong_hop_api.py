"""Bảng + biểu đồ load test API (median, min–max của 3 lần)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import _path  # noqa: F401
from mdl.report import load_runs, summarize, write_csv  # noqa: E402

plt.rcParams["font.family"] = "Segoe UI"
rows = sorted(summarize(load_runs("results/raw/tuan_10/runs_api_load.jsonl"), ["concurrency"],
                        ["qps", "p50_ms", "p95_ms", "p99_ms", "errors", "server_peak_rss_mb"]),
              key=lambda r: r["concurrency"])
write_csv(rows, "results/tables/t_api_load.csv")
fig, ax1 = plt.subplots(figsize=(6.4, 4))
c = [r["concurrency"] for r in rows]
ax1.errorbar(c, [r["qps_median"] for r in rows], yerr=[[r["qps_median"] - r["qps_min"] for r in rows],
             [r["qps_max"] - r["qps_median"] for r in rows]], marker="o", capsize=4, color="#4C78A8", label="QPS")
ax1.set_xscale("log")
ax1.set_xlabel("Số client đồng thời (log)")
ax1.set_ylabel("QPS", color="#4C78A8")
ax2 = ax1.twinx()
ax2.plot(c, [r["p95_ms_median"] for r in rows], marker="s", color="#E45756", label="P95 (ms)")
ax2.set_ylabel("P95 latency (ms)", color="#E45756")
ax1.set_title("API dữ liệu trên kho 982K bản ghi (median 3 lần)")
ax1.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("results/figures/h8_api_load.png", dpi=140)
for r in rows:
    print(r)
