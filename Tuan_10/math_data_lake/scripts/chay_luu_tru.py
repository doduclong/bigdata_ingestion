"""Thí nghiệm tuần 5: so sánh cấu hình lưu trữ trên toàn bộ dữ liệu curated.

1) Spark (local[4], driver 2 GB) ghi lại dữ liệu curated theo các layout L1..L4, compaction L4 -> L5.
2) DuckDB (4 luồng, 2 GB) chạy Q0..Q5 trên từng layout, lặp 3 lần; kiểm tra kết quả giống nhau giữa các layout.
Đầu vào: _storage/out/spark/full/math_record (tuần 4), _storage/out/baseline/full/math_record.jsonl (L0).
Chạy: python scripts/chay_luu_tru.py [--repeat 3]
"""
import argparse
import json
import shutil
from pathlib import Path

import _path  # noqa: F401
from mdl.config import STORAGE
from mdl.runlog import Monitor, make_run, new_run_id, write_run
from mdl.spark_etl import spark_session
from mdl.sql_queries import jsonl_source, parquet_source, run_sql_queries
from mdl.storage import LAYOUTS, compact, dir_stats, write_layout

ap = argparse.ArgumentParser()
ap.add_argument("--repeat", type=int, default=3)
ap.add_argument("--skip-write", action="store_true", help="chỉ chạy lại phần truy vấn")
ap.add_argument("--runs", default="results/raw/runs_storage.jsonl")
ap.add_argument("--layouts", nargs="+", default=None, help="chỉ chạy các layout này (mặc định: tất cả)")
a = ap.parse_args()

SRC = STORAGE / "out" / "spark" / "full" / "math_record"
OUT = STORAGE / "out" / "layouts"
L0 = STORAGE / "out" / "baseline" / "full" / "math_record.jsonl"
MANIFEST = "manifest/manifest_full.json"
ids = json.load(open("configs/query_ids.json"))["ids"]
Path("logs").mkdir(exist_ok=True)
paths = {"L0_jsonl": L0, **{k: OUT / k for k in LAYOUTS if k != "L0_jsonl"}}

if not a.skip_write:
    source_bytes = {}
    for d in SRC.glob("source=*/source_version=*"):
        source_bytes[(d.parent.name.split("=", 1)[1], d.name.split("=", 1)[1])] = sum(
            p.stat().st_size for p in d.glob("*.parquet"))
    spark = spark_session(master="local[4]", driver_memory="2g", app="mdl-storage")
    df = spark.read.parquet(str(SRC))
    for layout in ["L1_parquet_flat", "L2_parquet_src_ver", "L3_parquet_src_ver_subset", "L4_parquet_small_files",
                   "L6_parquet_src_ver_rg16"]:
        if a.layouts and layout not in a.layouts:
            continue
        rid = new_run_id(f"write-{layout}")
        with Monitor() as m:
            secs = write_layout(spark, df, paths[layout], layout, source_bytes)
        st = dir_stats(paths[layout])
        st["rows"] = spark.read.parquet(str(paths[layout])).count()
        write_run(a.runs, make_run(rid, "storage_write", {"layout": layout, "scale": "full", "writer": "spark-local4"},
                                   {**m.metrics(), "write_s": secs, **st}, "ok", "-", MANIFEST))
        print(layout, secs, st, flush=True)
    if not a.layouts or "L5_parquet_compacted" in a.layouts:
        # L5: sao chép L4 rồi compaction tại chỗ
        shutil.rmtree(paths["L5_parquet_compacted"], ignore_errors=True)
        shutil.copytree(paths["L4_parquet_small_files"], paths["L5_parquet_compacted"])
        rid = new_run_id("compact")
        with Monitor() as m:
            c = compact(spark, paths["L5_parquet_compacted"])
        st = dir_stats(paths["L5_parquet_compacted"])
        st["rows"] = spark.read.parquet(str(paths["L5_parquet_compacted"])).count()
        write_run(a.runs, make_run(rid, "storage_write", {"layout": "L5_parquet_compacted", "scale": "full",
                                                          "writer": "spark-local4 compaction"},
                                   {**m.metrics(), "write_s": c["compaction_s"], **c, **st}, "ok", "-", MANIFEST))
        print("L5", c, st, flush=True)
    spark.stop()
    if not a.layouts or "L0_jsonl" in a.layouts:
        st = {"files": 1, "bytes": L0.stat().st_size, "partitions": 1,
              "avg_file_mb": round(L0.stat().st_size / 2**20, 1)}
        write_run(a.runs, make_run(new_run_id("write-L0"), "storage_write", {"layout": "L0_jsonl", "scale": "full",
                                                                           "writer": "baseline (tuần 4)"},
                                   {**st, "rows": 982477}, "ok", "-", MANIFEST))

reference = None
if a.layouts and "L0_jsonl" not in a.layouts:  # vẫn cần kết quả L0 làm mốc so khớp (không ghi thành lần chạy)
    reference = {k: v["result"] for k, v in run_sql_queries(jsonl_source(L0.as_posix()), ids, threads=4).items()}
for layout, p in paths.items():
    if a.layouts and layout not in a.layouts:
        continue
    src = jsonl_source(p.as_posix()) if layout == "L0_jsonl" else parquet_source(p.as_posix())
    for i in range(a.repeat):
        rid = new_run_id(f"query-{layout}")
        with Monitor() as m:
            q = run_sql_queries(src, ids, threads=4)
        results = {k: v["result"] for k, v in q.items()}
        if reference is None:
            reference = results
        same = {k: json.dumps(results[k], default=str) == json.dumps(reference[k], default=str) for k in results}
        metrics = {**m.metrics(), **{k: v["seconds"] for k, v in q.items()},
                   "query_total_s": round(sum(v["seconds"] for v in q.values()), 4),
                   "results_match_L0": all(same.values()), "mismatch": [k for k, ok in same.items() if not ok]}
        log = Path("logs") / f"{rid}.log"
        log.write_text(json.dumps({"metrics": metrics, "results": results}, ensure_ascii=False, default=str, indent=1),
                       encoding="utf-8")
        write_run(a.runs, make_run(rid, "storage_query", {"layout": layout, "scale": "full", "engine": "duckdb-4t",
                                                          "repeat_idx": i}, metrics, "ok", log, MANIFEST))
        print(layout, i, metrics["query_total_s"], {k: v["seconds"] for k, v in q.items()}, metrics["mismatch"],
              flush=True)
