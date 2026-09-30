"""Bảng + biểu đồ tuần 5 từ results/raw/runs_storage.jsonl (median 3 lần cho truy vấn)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import _path  # noqa: F401
from mdl.report import load_runs, summarize, write_csv  # noqa: E402

plt.rcParams["font.family"] = "Segoe UI"
runs = load_runs("results/raw/runs_storage.jsonl")
Q = ["Q0_full_scan", "Q1_count_by_source_split", "Q2_olympiad_latex", "Q3_point_lookup", "Q4_top_premises",
     "Q5_provenance_audit"]
writes = {r["parameters"]["layout"]: r["metrics"] for r in runs if r["experiment"] == "storage_write"}
qrows = {r["layout"]: r for r in summarize([r for r in runs if r["experiment"] == "storage_query"], ["layout"],
                                           Q + ["query_total_s", "peak_rss_mb"])}
order = sorted(writes)
rows = []
for L in order:
    w, q = writes[L], qrows.get(L, {})
    rows.append({"layout": L, "files": w.get("files"), "partitions": w.get("partitions"),
                 "size_mb": round(w["bytes"] / 2**20, 1), "avg_file_mb": w.get("avg_file_mb"),
                 "small_files_lt_8mb": w.get("small_files_lt_8mb"), "write_s": w.get("write_s"),
                 "rows": w.get("rows"), "query_total_s_median": q.get("query_total_s_median"),
                 "query_total_s_min": q.get("query_total_s_min"), "query_total_s_max": q.get("query_total_s_max"),
                 **{f"{k}_median": q.get(f"{k}_median") for k in Q}})
write_csv(rows, "results/tables/storage_layouts.csv")

short = [L.split("_", 1)[0] for L in order]
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
axes[0].bar(short, [r["size_mb"] for r in rows], color="#4C78A8")
axes[0].set_title("Dung lượng (MB)")
axes[1].bar(short, [r["files"] for r in rows], color="#F58518")
axes[1].set_yscale("log")
axes[1].set_title("Số tệp (log)")
axes[2].bar(short, [r["query_total_s_median"] for r in rows], color="#54A24B",
            yerr=[[r["query_total_s_median"] - r["query_total_s_min"] for r in rows],
                  [r["query_total_s_max"] - r["query_total_s_median"] for r in rows]], capsize=3)
axes[2].set_yscale("log")
axes[2].set_title("Tổng Q0–Q5, DuckDB (s, log)")
for ax in axes:
    ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("results/figures/w5_layouts.png", dpi=140)

fig, ax = plt.subplots(figsize=(10, 4.2))
width = 0.12
for j, L in enumerate(order):
    ax.bar([i + j * width for i in range(len(Q))], [qrows[L][f"{k}_median"] for k in Q], width, label=short[j])
ax.set_xticks([i + width * (len(order) - 1) / 2 for i in range(len(Q))])
ax.set_xticklabels([k.split("_", 1)[0] for k in Q])
ax.set_yscale("log")
ax.set_ylabel("Thời gian median (s, log)")
ax.set_title("Thời gian từng truy vấn theo layout (DuckDB, 4 luồng)")
ax.legend(ncol=7, fontsize=8)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("results/figures/w5_queries.png", dpi=140)
for r in rows:
    print(r)
