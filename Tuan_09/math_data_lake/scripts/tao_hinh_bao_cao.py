"""Sinh mọi hình và bảng của báo cáo từ results/raw/tuan_XX (không nhập số bằng tay).

Chạy: python scripts/tao_hinh_bao_cao.py   ->  results/figures/*.png, results/tables/*.csv
"""
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

import _path  # noqa: F401
from mdl.report import SCALE_N, load_runs, plot_scale, summarize, write_csv  # noqa: E402

plt.rcParams["font.family"] = "Segoe UI"
RAW, FIG, TAB = "results/raw/", "results/figures/", "results/tables/"

# Hình 1: kiến trúc
fig, ax = plt.subplots(figsize=(13, 3.4))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
stages = [("Nguồn", ["HF NuminaMath", "GitHub ProofNet", "Zenodo LeanDojo"], "#E8F1FB"),
          ("Raw zone", ["tệp gốc bất biến", "manifest sha256", "license, ngày tải"], "#FDF1E3"),
          ("Staging", ["JSONL UTF-8 NFC", "con trỏ raw", "corpus Lean"], "#EAF7EA"),
          ("Spark ETL", ["biểu thức JVM", "kiểm lỗi E01–E06", "provenance join"], "#FBE8EF"),
          ("Curated lake", ["Parquet zstd", "source/version", "_lake_log, compaction"], "#F4F4F4"),
          ("Phục vụ", ["catalog, data card", "DuckDB / API", "truy vết provenance"], "#EFEAFB")]
w, gap = 0.14, 0.025
for i, (t, ls, c) in enumerate(stages):
    x = 0.01 + i * (w + gap)
    ax.add_patch(FancyBboxPatch((x, 0.1), w, 0.78, boxstyle="round,pad=0.02", fc=c, ec="#333"))
    ax.text(x + w / 2, 0.82, t, ha="center", va="top", fontsize=11, weight="bold")
    for j, s in enumerate(ls):
        ax.text(x + w / 2, 0.6 - j * 0.15, s, ha="center", fontsize=8.5)
    if i:
        ax.annotate("", xy=(x, 0.5), xytext=(x - gap, 0.5), arrowprops=dict(arrowstyle="->", lw=1.4))
fig.savefig(FIG + "h1_kien_truc.png", dpi=140, bbox_inches="tight")
plt.close(fig)

# Hình 2–4: quy mô (tuần 7)
runs = load_runs(RAW + "tuan_07/runs_baseline.jsonl", RAW + "tuan_07/runs_spark.jsonl")
for r in runs:
    p, m = r["parameters"], r["metrics"]
    p["method"] = f"Spark {p['workers']} nhân" if r["experiment"] == "spark_etl" else "Baseline Python 1 nhân"
    m["throughput_e2e"] = round(m["records_in"] / m["runtime_s"], 1)
rows = sorted(summarize(runs, ["method", "scale"], ["runtime_s", "throughput_e2e", "peak_rss_mb", "query_total_s",
                                                    "sql_total_s", "read_bytes", "write_bytes", "bytes_out"]),
              key=lambda r: (r["method"], SCALE_N[r["scale"]]))
write_csv(rows, TAB + "t_quy_mo.csv")
plot_scale(rows, "runtime_s", "Runtime end-to-end (s)", FIG + "h2_runtime.png", series_key="method", logy=True)
plot_scale(rows, "peak_rss_mb", "Peak RSS (MB)", FIG + "h3_peak_rss.png", series_key="method")
q = []
for r in rows:
    if r["method"].startswith("Baseline"):
        q += [{**r, "engine": "Python quét JSONL", **{f"q_{s}": r[f"query_total_s_{s}"] for s in ("median", "min", "max")}},
              {**r, "engine": "DuckDB trên JSONL", **{f"q_{s}": r[f"sql_total_s_{s}"] for s in ("median", "min", "max")}}]
    elif r["method"] == "Spark 4 nhân":
        q.append({**r, "engine": "DuckDB trên Parquet", **{f"q_{s}": r[f"sql_total_s_{s}"] for s in ("median", "min", "max")}})
plot_scale(q, "q", "Thời gian bộ truy vấn kiểm tra (s)", FIG + "h4_truy_van.png", series_key="engine", logy=True)

# Hình 5: lưu trữ (tuần 8, 3 lần)
st = load_runs(RAW + "tuan_08/runs_storage_x3.jsonl")
wr = {r["layout"]: r for r in summarize([r for r in st if r["experiment"] == "storage_write"], ["layout"],
                                        ["bytes", "files"])}
qr = {r["layout"]: r for r in summarize([r for r in st if r["experiment"] == "storage_query"], ["layout"],
                                        ["query_total_s"])}
order = sorted(wr)
write_csv([{"layout": L, "files": wr[L]["files_median"], "size_mb": round(wr[L]["bytes_median"] / 2**20, 1),
            "query_total_s_median": qr[L]["query_total_s_median"]} for L in order], TAB + "t_luu_tru.csv")
fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
short = [L.split("_", 1)[0] for L in order]
for ax, vals, title, log in ((axes[0], [wr[L]["bytes_median"] / 2**20 for L in order], "Dung lượng (MB)", False),
                             (axes[1], [wr[L]["files_median"] for L in order], "Số tệp (log)", True),
                             (axes[2], [qr[L]["query_total_s_median"] for L in order], "Tổng Q0–Q5 DuckDB (s, log)", True)):
    ax.bar(short, vals, color="#4C78A8")
    ax.set_title(title)
    if log:
        ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(FIG + "h5_luu_tru.png", dpi=140)
plt.close(fig)

# Hình 6: phân rã giai đoạn (tuần 8)
ab = load_runs(RAW + "tuan_08/runs_ablation.jsonl")
bd = [r["metrics"] for r in ab if r["experiment"] == "stage_breakdown"]
e0 = statistics.median(r["metrics"]["elapsed_s"] for r in ab if r["parameters"].get("config") == "E0_mac_dinh")
b1, b2, b3 = (statistics.median(m[k] for m in bd) for k in
              ("B1_doc_parse_json", "B2_anh_xa_khong_kiem_trung", "B3_anh_xa_co_kiem_trung"))
stages = {"Đọc + parse JSON": b1, "Ánh xạ, regex, join": b2 - b1, "Kiểm tra trùng khóa": b3 - b2,
          "Ghi Parquet zstd": e0 - b3}
write_csv([{"giai_doan": k, "giay": round(v, 2)} for k, v in stages.items()], TAB + "t_phan_ra.csv")
fig, ax = plt.subplots(figsize=(10, 2.6))
left = 0
for (k, v), c in zip(stages.items(), ["#4C78A8", "#F58518", "#E45756", "#54A24B"]):
    ax.barh([0], [v], left=left, color=c, label=f"{k}: {v:.1f} s")
    left += v
ax.set_yticks([])
ax.set_title(f"Phân rã thời gian Spark ETL toàn bộ dữ liệu — {e0:.1f} s (median 3 lần, local[4])")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=4, fontsize=8)
fig.savefig(FIG + "h6_phan_ra.png", dpi=140, bbox_inches="tight")
plt.close(fig)

# Hình 7: nạp gia tăng (tuần 6)
inc = load_runs(RAW + "tuan_06/runs_incremental.jsonl")
g = {}
for r in inc:
    key = "Dựng lại\ntoàn bộ" if r["experiment"] == "full_rebuild" else (
        {"v0": "v0 nạp\nban đầu", "v1": "v1 batch mới\n171.898", "v2": "v2 nạp lại\n(idempotent)"}.get(
            r["parameters"].get("step")))
    if key:
        g.setdefault(key, []).append(r["metrics"]["runtime_s"])
fig, ax = plt.subplots(figsize=(8, 3.4))
ys = [statistics.median(v) for v in g.values()]
ax.bar(list(g), ys, color=["#999999", "#4C78A8", "#54A24B", "#F58518"])
for i, v in enumerate(ys):
    ax.text(i, v + 1, f"{v:.1f} s", ha="center")
ax.set_ylabel("Runtime (s), median 3 lần")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(FIG + "h7_gia_tang.png", dpi=140)
plt.close(fig)
print("OK — hình trong", FIG, "bảng trong", TAB)
