"""Thí nghiệm tuần 6: cập nhật gia tăng + catalog + truy vết provenance.

Kịch bản (dữ liệu thật): batch mới = shard NuminaMath train-00004 (171.898 bản ghi).
  v0  nạp ban đầu: mọi staging trừ shard 4
  v1  nạp batch shard 4                    -> kỳ vọng 171.898 mới
  v2  nạp lại đúng batch shard 4           -> kỳ vọng 0 mới, 171.898 không đổi (idempotent)
  So sánh: kho sau v2 phải trùng (record_id, content_sha256) với bản dựng lại toàn bộ; so chi phí với dựng lại.
Chạy: python scripts/chay_gia_tang.py --repeat 3
"""
import argparse
import json
import os
import shutil
from pathlib import Path

import duckdb

import _path  # noqa: F401
from mdl.catalog import build_catalog, catalog_markdown
from mdl.config import STAGING, STORAGE
from mdl.lake import ingest_batch, new_run_id
from mdl.manifest import load_manifest
from mdl.provenance import trace
from mdl.runlog import Monitor, make_run, write_run
from mdl.spark_etl import run_spark_etl, spark_session

ap = argparse.ArgumentParser()
ap.add_argument("--repeat", type=int, default=3)
ap.add_argument("--runs", default="results/raw/runs_incremental.jsonl")
a = ap.parse_args()

MANIFEST_PATH = "manifest/manifest_full.json"
manifest = load_manifest(MANIFEST_PATH)
BATCH_FILE = "part-train-00004-of-00005.jsonl"
INIT, BATCH = STORAGE / "staging_w6_initial", STORAGE / "staging_w6_batch"
LAKE, FULL = STORAGE / "lake_w6", STORAGE / "out" / "w6_full_rebuild"


def link_tree(src_root, dst_root, keep):
    shutil.rmtree(dst_root, ignore_errors=True)
    for p in Path(src_root).rglob("*.jsonl"):
        if keep(p):
            d = dst_root / p.relative_to(src_root)
            d.parent.mkdir(parents=True, exist_ok=True)
            os.link(p, d)  # liên kết cứng: không nhân đôi dữ liệu trên đĩa


link_tree(STAGING, INIT, lambda p: p.name != BATCH_FILE)
link_tree(STAGING, BATCH, lambda p: p.name == BATCH_FILE)


def compare(lake_table, full_table):
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'; SET threads=4")
    q = lambda p: f"(SELECT record_id, source_version, content_sha256 FROM read_parquet('{p.as_posix()}/**/*.parquet', hive_partitioning=true))"  # noqa: E501,E731
    return {
        "lake_rows": con.execute(f"SELECT count(*) FROM {q(lake_table)}").fetchone()[0],
        "lake_distinct_keys": con.execute(f"SELECT count(DISTINCT (record_id, source_version)) FROM {q(lake_table)}").fetchone()[0],
        "full_rows": con.execute(f"SELECT count(*) FROM {q(full_table)}").fetchone()[0],
        "only_in_lake": con.execute(f"SELECT count(*) FROM ({q(lake_table)} EXCEPT {q(full_table)})").fetchone()[0],
        "only_in_full": con.execute(f"SELECT count(*) FROM ({q(full_table)} EXCEPT {q(lake_table)})").fetchone()[0],
    }


spark = spark_session(master="local[4]", driver_memory="2g", app="mdl-incremental")
Path("logs").mkdir(exist_ok=True)
for i in range(a.repeat):
    # Dựng lại toàn bộ (mốc so sánh chi phí và đúng đắn)
    rid = new_run_id()
    with Monitor() as m:
        res = run_spark_etl(spark, STAGING, FULL, manifest, rid)
    write_run(a.runs, make_run(rid, "full_rebuild", {"repeat_idx": i, "records": res["records_in"]},
                               {**m.metrics(), **res}, "ok", "-", MANIFEST_PATH))
    print("full rebuild", m.metrics()["runtime_s"], flush=True)
    shutil.rmtree(LAKE, ignore_errors=True)
    for step, (stg, name) in enumerate([(INIT, "v0 nạp ban đầu (trừ NuminaMath shard 4)"),
                                        (BATCH, "v1 batch mới NuminaMath shard 4"),
                                        (BATCH, "v2 nạp lại batch shard 4 (idempotent)")]):
        rid = new_run_id()
        with Monitor() as m:
            entry = ingest_batch(spark, stg, LAKE, manifest, rid, name)
        write_run(a.runs, make_run(rid, "incremental_ingest", {"repeat_idx": i, "step": f"v{step}", "batch": name},
                                   {**m.metrics(), **entry}, "ok", "-", MANIFEST_PATH))
        agg = {k: sum(p[k] for p in entry["partitions"].values()) for k in ("new", "unchanged", "conflict")}
        print(name, m.metrics()["runtime_s"], agg, entry["compaction"], flush=True)
    cmp = compare(LAKE / "math_record", FULL / "math_record")
    write_run(a.runs, make_run(new_run_id(), "incremental_verify", {"repeat_idx": i}, cmp, "ok", "-", MANIFEST_PATH))
    print("verify", cmp, flush=True)
spark.stop()

print("Tiếp theo: python scripts/tao_catalog.py")
