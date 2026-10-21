"""Chạy Spark ETL trên các mức quy mô, lặp N lần, ghi raw results theo Phụ lục B.

Chạy: python scripts/chay_spark.py --scales 10k 100k full --repeat 3 --cores 4
"""
import argparse
import json
import shutil
import time
from pathlib import Path

import _path  # noqa: F401
from mdl.config import STAGING, STORAGE
from mdl.manifest import load_manifest
from mdl.runlog import Monitor, make_run, new_run_id, write_run
from mdl.spark_etl import run_spark_etl, spark_session
from mdl.sql_queries import parquet_source, run_sql_queries

ap = argparse.ArgumentParser()
ap.add_argument("--scales", nargs="+", default=["10k", "100k", "full"])
ap.add_argument("--repeat", type=int, default=3)
ap.add_argument("--cores", type=int, default=4)
ap.add_argument("--driver-memory", default="2g", help="giữ <= 2g: tổng RAM phải dưới 4 GB")
ap.add_argument("--max-partition-mb", type=int, default=128, help="spark.sql.files.maxPartitionBytes")
ap.add_argument("--repartition", type=int, default=None)
ap.add_argument("--max-records-per-file", type=int, default=None)
ap.add_argument("--partition-cols", default="source,source_version", help="'' = không partition")
ap.add_argument("--no-dup-check", action="store_true")
ap.add_argument("--queries", action="store_true", help="chạy thêm Q0-Q5 bằng DuckDB trên Parquet vừa ghi")
ap.add_argument("--tag", default="spark")
ap.add_argument("--runs", default="results/raw/runs_spark.jsonl")
ap.add_argument("--out-name", default=None, help="thư mục con trong _storage/out (mặc định = tag)")
a = ap.parse_args()

manifest = load_manifest("manifest/manifest_full.json")
pcols = tuple(c for c in a.partition_cols.split(",") if c)
Path("logs").mkdir(exist_ok=True)
for scale in a.scales:
    src = STAGING if scale == "full" else STORAGE / "staging_scales" / f"n={scale}"
    for i in range(a.repeat):
        rid = new_run_id(f"{a.tag}-{scale}")
        out = STORAGE / "out" / (a.out_name or a.tag) / scale
        shutil.rmtree(out, ignore_errors=True)
        log = Path("logs") / f"{rid}.log"
        params = {"scale": scale, "repeat_idx": i, "input": str(src), "format": "parquet-zstd",
                  "partitioning": "/".join(pcols) or "none", "workers": a.cores, "driver_memory": a.driver_memory,
                  "max_partition_mb": a.max_partition_mb, "repartition": a.repartition,
                  "max_records_per_file": a.max_records_per_file, "dup_check": not a.no_dup_check, "tag": a.tag}
        status, res = "ok", {}
        try:
            with Monitor() as m:
                t0 = time.perf_counter()
                spark = spark_session(master=f"local[{a.cores}]", driver_memory=a.driver_memory,
                                      extra={"spark.sql.files.maxPartitionBytes": f"{a.max_partition_mb}m"})
                startup = time.perf_counter() - t0
                res = run_spark_etl(spark, src, out, manifest, rid, repartition=a.repartition,
                                    max_records_per_file=a.max_records_per_file, partition_cols=pcols,
                                    check_duplicates=not a.no_dup_check)
                spark.stop()
            res["spark_startup_s"] = round(startup, 3)
            status = res["status"]
        except (Exception, KeyboardInterrupt) as e:  # gồm cả ngắt do chốt chặn RAM
            status = f"failed: {type(e).__name__}: {str(e)[:300]}"
            m = None
        metrics = {**(m.metrics() if m else {}), **res}
        if a.queries and status == "ok":
            ids = json.load(open("configs/query_ids.json"))["ids"]
            q = run_sql_queries(parquet_source((out / "math_record").as_posix()), ids, threads=4)
            metrics.update({f"sql_{k}": v["seconds"] for k, v in q.items()})
            metrics["sql_total_s"] = round(sum(v["seconds"] for v in q.values()), 4)
        if "elapsed_s" in res:  # throughput tính trên thời gian ETL (không gồm khởi động JVM)
            metrics["throughput_rps"] = res["throughput_rps"]
        log.write_text(json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8")
        write_run(a.runs, make_run(rid, "spark_etl", params, metrics, status, log, "manifest/manifest_full.json"))
        print(f"{rid} {status} total={metrics.get('runtime_s')}s etl={metrics.get('elapsed_s')}s "
              f"thr={metrics.get('throughput_rps')} rss={metrics.get('peak_rss_mb')}MB files={metrics.get('files_out')}",
              flush=True)
