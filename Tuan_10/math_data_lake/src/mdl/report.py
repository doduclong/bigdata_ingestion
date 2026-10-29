"""Tổng hợp raw results (JSONL lần chạy) thành bảng median/min/max và biểu đồ — không chỉnh số bằng tay."""
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, StrMethodFormatter  # noqa: E402

plt.rcParams["font.family"] = "Segoe UI"
SCALE_N = {"10k": 10_000, "100k": 100_000, "500k": 500_000, "full": 982_482}


def load_runs(*paths):
    runs = []
    for p in paths:
        if Path(p).exists():
            runs += [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    return runs


def summarize(runs, group_keys, metrics):
    """Nhóm theo các tham số `group_keys`; với mỗi metric trả median, min, max, n (chỉ lần chạy status=ok)."""
    groups = {}
    for r in runs:
        if r["status"] != "ok":
            continue
        k = tuple(r["parameters"].get(g) for g in group_keys)
        groups.setdefault(k, []).append(r)
    rows = []
    for k, rs in groups.items():
        row = dict(zip(group_keys, k))
        row["n_runs"] = len(rs)
        for m in metrics:
            vals = [r["metrics"][m] for r in rs if r["metrics"].get(m) is not None]
            if vals:
                row[f"{m}_median"] = statistics.median(vals)
                row[f"{m}_min"] = min(vals)
                row[f"{m}_max"] = max(vals)
        rows.append(row)
    return rows


def write_csv(rows, path):
    import csv
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cols = []
    for r in rows:
        cols += [c for c in r if c not in cols]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def plot_scale(rows, metric, ylabel, path, series_key=None, logx=True, logy=False, title=None, show_values=False):
    """Trục x = số bản ghi; điểm = median; thanh lỗi = min–max."""
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    series = {}
    for r in rows:
        series.setdefault(r.get(series_key) if series_key else "baseline", []).append(r)
    for name, rs in series.items():
        rs = sorted((r for r in rs if f"{metric}_median" in r), key=lambda r: SCALE_N[r["scale"]])
        if not rs:
            continue
        x = [SCALE_N[r["scale"]] for r in rs]
        y = [r[f"{metric}_median"] for r in rs]
        lo = [r[f"{metric}_median"] - r[f"{metric}_min"] for r in rs]
        hi = [r[f"{metric}_max"] - r[f"{metric}_median"] for r in rs]
        line = ax.errorbar(x, y, yerr=[lo, hi], marker="o", capsize=4, label=str(name))
        if show_values:
            for xi, yi in zip(x, y):
                label = f"{yi:,.2f}".rstrip("0").rstrip(".")
                ax.annotate(label, (xi, yi), xytext=(0, 8), textcoords="offset points",
                            ha="center", fontsize=8, color=line[0].get_color())
    if logx:
        ax.set_xscale("log")
    else:
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    if logy:
        ax.set_yscale("log")
    else:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.10f}".rstrip("0").rstrip(".")))
    ax.set_xlabel("Số bản ghi (log)" if logx else "Số bản ghi")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    ax.set_title(title or ylabel)
    if len(series) > 1:
        ax.legend(fontsize=8)
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
