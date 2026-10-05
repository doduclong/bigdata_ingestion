"""Bảng + biểu đồ tuần 6: chi phí nạp gia tăng so với dựng lại toàn bộ (median, min–max của 3 lần)."""
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import _path  # noqa: F401
from mdl.report import load_runs, write_csv  # noqa: E402

plt.rcParams["font.family"] = "Segoe UI"
runs = load_runs("results/raw/runs_incremental.jsonl")
groups = {}
for r in runs:
    if r["experiment"] == "full_rebuild":
        groups.setdefault("Dựng lại toàn bộ (982.477)", []).append(r)
    elif r["experiment"] == "incremental_ingest":
        groups.setdefault(r["parameters"]["batch"], []).append(r)
rows = []
for name, rs in groups.items():
    rt = [r["metrics"]["runtime_s"] for r in rs]
    m = rs[0]["metrics"]
    parts = m.get("partitions", {})
    comp = [r["metrics"]["compaction"]["compaction_s"] for r in rs if r["metrics"].get("compaction")]
    rows.append({"buoc": name, "n_runs": len(rs), "runtime_median_s": statistics.median(rt), "runtime_min_s": min(rt),
                 "runtime_max_s": max(rt),
                 "peak_rss_mb_max": max(r["metrics"]["peak_rss_mb"] for r in rs),
                 "new": sum(p["new"] for p in parts.values()) if parts else m.get("records_out"),
                 "unchanged": sum(p["unchanged"] for p in parts.values()) if parts else None,
                 "conflict": sum(p["conflict"] for p in parts.values()) if parts else None,
                 "files_added": m.get("files_added", m.get("files_out")),
                 "compaction_median_s": statistics.median(comp) if comp else None})
verify = [r["metrics"] for r in runs if r["experiment"] == "incremental_verify"]
write_csv(rows, "results/tables/incremental.csv")
fig, ax = plt.subplots(figsize=(9, 3.8))
labels = ["Dựng lại\ntoàn bộ", "v0 nạp\nban đầu", "v1 batch mới\n(171.898)", "v2 nạp lại\n(idempotent)"]
y = [r["runtime_median_s"] for r in rows]
err = [[r["runtime_median_s"] - r["runtime_min_s"] for r in rows], [r["runtime_max_s"] - r["runtime_median_s"] for r in rows]]
ax.bar(labels, y, yerr=err, capsize=4, color=["#999999", "#4C78A8", "#54A24B", "#F58518"])
for i, v in enumerate(y):
    ax.text(i, v + 1, f"{v:.1f} s", ha="center")
ax.set_ylabel("Runtime end-to-end (s)")
ax.set_title("Nạp gia tăng so với dựng lại toàn bộ (median 3 lần, Spark local[4], 2 GB)")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("results/figures/w6_incremental.png", dpi=140)
for r in rows:
    print(r)
print(verify)
