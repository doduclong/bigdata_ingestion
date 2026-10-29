"""Bảng + biểu đồ tuần 5 từ results/raw/runs_storage.jsonl (median 3 lần cho truy vấn)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator, NullFormatter  # noqa: E402
from pathlib import Path  # noqa: E402

import _path  # noqa: F401
from mdl.report import load_runs, summarize, write_csv  # noqa: E402

plt.rcParams["font.family"] = "Segoe UI"


def number(value, digits=3):
    text = f"{value:.{digits}f}"
    return (text.rstrip("0").rstrip(".") if digits else text).replace(".", ",")


def format_axis(ax, log=False, integer=False):
    if log:
        ax.set_yscale("log")
        ax.yaxis.set_minor_formatter(NullFormatter())
    else:
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=integer))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: number(value, 0 if integer else 4)))
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)


def label_bars(ax, bars, digits=3):
    ax.bar_label(bars, labels=[number(b.get_height(), digits) for b in bars], padding=5, fontsize=9)


def plot_layouts(rows):
    labels = [r["layout"].split("_", 1)[0] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    specs = [("size_mb", "Dung lượng (MiB)", "#4C78A8", False, 1),
             ("files", "Số tệp (trục log)", "#F58518", True, 0),
             ("query_total_s_median", "Tổng Q0–Q5: median (giây, trục log)", "#54A24B", True, 3)]
    for ax, (key, title, color, log, digits) in zip(axes, specs):
        values = [r[key] for r in rows]
        errors = None
        if key == "query_total_s_median":
            errors = [[r[key] - r["query_total_s_min"] for r in rows],
                      [r["query_total_s_max"] - r[key] for r in rows]]
        bars = ax.bar(labels, values, color=color, yerr=errors, capsize=3)
        format_axis(ax, log=log, integer=key == "files")
        label_bars(ax, bars, digits)
        upper = max(r["query_total_s_max"] for r in rows) if errors else max(values)
        ax.set_ylim(top=upper * 1.35)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Cấu hình lưu trữ")
    fig.tight_layout()
    fig.savefig("results/figures/w5_layouts.png", dpi=180)
    plt.close(fig)


def plot_queries(rows):
    labels = [r["layout"].split("_", 1)[0] for r in rows]
    titles = ["Q0 — Quét toàn bộ", "Q1 — Đếm theo nguồn/split", "Q2 — Lọc bài toán LaTeX",
              "Q3 — Tra cứu record_id", "Q4 — Top premise", "Q5 — Kiểm tra provenance"]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    colors = [f"C{i}" for i in range(len(rows))]
    for ax, query, title in zip(axes.flat, Q, titles):
        values = [r[f"{query}_median"] for r in rows]
        bars = ax.bar(labels, values, color=colors)
        format_axis(ax)
        label_bars(ax, bars, digits=4)
        ax.set_ylim(top=max(values) * 1.25)
        ax.set_title(title)
        ax.set_ylabel("Thời gian median (giây)")
    fig.suptitle("Thời gian từng truy vấn — trục tuyến tính; mỗi ô có thang đo riêng", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig("results/figures/w5_queries.png", dpi=180)
    plt.close(fig)


def plot_parquet_files(rows):
    parquet = [r for r in rows if r["layout"] != "L0_jsonl"]
    labels = [r["layout"].split("_", 1)[0] for r in parquet]
    values = [r["files"] for r in parquet]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(labels, values, color=["#F58518" if label == "L4" else "#4C78A8" for label in labels])
    ax.bar_label(bars, labels=[number(v, 0) for v in values], padding=5)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.15)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: number(value, 0)))
    ax.set_xlabel("Số file Parquet (trục tuyến tính)")
    ax.set_title("Số file Parquet theo cấu hình — L4 tạo file nhỏ, L5 sau compaction")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig("results/figures/w5_parquet_files.png", dpi=180)
    plt.close(fig)


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

Path("results/figures").mkdir(parents=True, exist_ok=True)
plot_layouts(rows)
plot_queries(rows)
plot_parquet_files(rows)
for r in rows:
    print(r)
