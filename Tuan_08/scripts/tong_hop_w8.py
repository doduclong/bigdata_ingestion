"""Bảng ablation + biểu đồ phân rã thời gian tuần 8 (median, min–max của 3 lần)."""
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import _path  # noqa: F401
from mdl.report import load_runs, summarize, write_csv  # noqa: E402

plt.rcParams["font.family"] = "Segoe UI"
runs = load_runs("results/raw/runs_ablation.jsonl")
Q = ["Q0_full_scan", "Q1_count_by_source_split", "Q2_olympiad_latex", "Q3_point_lookup", "Q4_top_premises",
     "Q5_provenance_audit"]
rows = summarize([r for r in runs if r["experiment"] == "ablation_etl"], ["config"],
                 ["runtime_s", "elapsed_s", "peak_rss_mb", "read_bytes", "write_bytes", "bytes_out", "files_out",
                  "sql_total_s"] + Q)
base = next(r for r in rows if r["config"] == "E0_mac_dinh")
table = []
for r in sorted(rows, key=lambda r: r["config"]):
    table.append({
        "config": r["config"], "n_runs": r["n_runs"],
        "etl_s_median": r["elapsed_s_median"], "etl_s_min": r["elapsed_s_min"], "etl_s_max": r["elapsed_s_max"],
        "delta_etl_vs_E0_pct": round(100 * (r["elapsed_s_median"] / base["elapsed_s_median"] - 1), 1),
        "size_mb": round(r["bytes_out_median"] / 2**20, 1), "files": r["files_out_median"],
        "read_gb": round(r["read_bytes_median"] / 2**30, 2), "write_gb": round(r["write_bytes_median"] / 2**30, 2),
        "peak_rss_mb_max": r["peak_rss_mb_max"], "sql_total_s_median": r["sql_total_s_median"],
        "Q3_point_lookup_median": r["Q3_point_lookup_median"], "Q0_full_scan_median": r["Q0_full_scan_median"]})
write_csv(table, "results/tables/ablation.csv")

bd = [r["metrics"] for r in runs if r["experiment"] == "stage_breakdown"]
b1 = statistics.median(m["B1_doc_parse_json"] for m in bd)
b2 = statistics.median(m["B2_anh_xa_khong_kiem_trung"] for m in bd)
b3 = statistics.median(m["B3_anh_xa_co_kiem_trung"] for m in bd)
e0 = base["elapsed_s_median"]
stages = {"Đọc + parse JSON": b1, "Ánh xạ, regex, join corpus": b2 - b1, "Kiểm tra trùng khóa": b3 - b2,
          "Ghi Parquet zstd (+ quét lại)": e0 - b3}
write_csv([{"giai_doan": k, "giay": round(v, 2), "ty_le": round(v / e0, 3)} for k, v in stages.items()],
          "results/tables/stage_breakdown.csv")
fig, ax = plt.subplots(figsize=(9, 2.9))
left = 0
colors = ["#4C78A8", "#F58518", "#E45756", "#54A24B"]
for (k, v), c in zip(stages.items(), colors):
    ax.barh([0], [v], left=left, color=c, label=f"{k}: {v:.1f} s")
    left += v
ax.set_yticks([])
ax.set_xlabel("")
ax.set_title(f"Phân rã thời gian Spark ETL — tổng {e0:.1f} s (giây, median 3 lần, local[4], toàn bộ dữ liệu)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=8)
fig.tight_layout()
fig.savefig("results/figures/w8_stage_breakdown.png", dpi=140, bbox_inches="tight")

fig, axes = plt.subplots(1, 3, figsize=(14, 4))
names = [t["config"].split("_", 1)[0] for t in table]
for ax, key, title in zip(axes, ["etl_s_median", "size_mb", "sql_total_s_median"],
                          ["Thời gian ETL (s)", "Dung lượng đầu ra (MB)", "Tổng Q0–Q5 DuckDB (s)"]):
    ax.bar(names, [t[key] for t in table], color="#4C78A8")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("results/figures/w8_ablation.png", dpi=140)
for t in table:
    print(t)
print({k: round(v, 2) for k, v in stages.items()})
