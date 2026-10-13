"""Ablation định dạng / partition / kích thước tệp, 3 lần ghi + 3 lần truy vấn mỗi cấu hình (median, min–max)."""
import _path  # noqa: F401
from mdl.report import load_runs, summarize, write_csv

runs = load_runs("results/raw/runs_storage_x3.jsonl")
w = {r["layout"]: r for r in summarize([r for r in runs if r["experiment"] == "storage_write"], ["layout"],
                                       ["write_s", "bytes", "files", "small_files_lt_8mb", "rows"])}
q = {r["layout"]: r for r in summarize([r for r in runs if r["experiment"] == "storage_query"], ["layout"],
                                       ["query_total_s", "Q0_full_scan", "Q1_count_by_source_split", "Q3_point_lookup",
                                        "Q4_top_premises"])}
mism = sum(1 for r in runs if r["experiment"] == "storage_query" and not r["metrics"]["results_match_L0"])
rows = []
for L in sorted(w):
    a, b = w[L], q.get(L, {})
    rows.append({"layout": L, "n_write": a["n_runs"], "n_query": b.get("n_runs"),
                 "write_s_median": a.get("write_s_median"), "write_s_min": a.get("write_s_min"),
                 "write_s_max": a.get("write_s_max"), "files": a["files_median"],
                 "size_mb": round(a["bytes_median"] / 2**20, 1), "rows": a["rows_median"],
                 "query_total_s_median": b.get("query_total_s_median"), "query_total_s_min": b.get("query_total_s_min"),
                 "query_total_s_max": b.get("query_total_s_max"), "Q1_median": b.get("Q1_count_by_source_split_median"),
                 "Q4_median": b.get("Q4_top_premises_median")})
write_csv(rows, "results/tables/storage_ablation_x3.csv")
for r in rows:
    print(r)
print("query result mismatches vs L0:", mism)
