"""Tuần 8 — ablation Spark ETL và phân rã thời gian theo giai đoạn (toàn bộ dữ liệu, 3 lần lặp).

A. Phân rã giai đoạn (ghi vào sink `noop` để không tốn I/O ghi):
   B1 chỉ đọc + parse JSON staging | B2 + ánh xạ/dẫn xuất (không kiểm trùng) | B3 + kiểm tra trùng khóa
B. Ablation cấu hình ghi (mỗi cấu hình đo cả thời gian ETL, dung lượng và Q0–Q5 DuckDB):
   E0 mặc định (kiểm trùng, row group 16 MB, split 128 MB, zstd) | E1 tắt kiểm trùng | E2 row group mặc định
   E3 split đầu vào 32 MB | E4 snappy | E5 không nén | E6 sắp xếp theo record_id trong tệp
Chạy: python scripts/chay_ablation.py --repeat 3
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
from mdl.spark_etl import _read, build_curated, run_spark_etl, spark_session, staging_schemas
from mdl.sql_queries import parquet_source, run_sql_queries

ap = argparse.ArgumentParser()
ap.add_argument("--repeat", type=int, default=3)
ap.add_argument("--only", nargs="*", default=None)
ap.add_argument("--runs", default="results/raw/runs_ablation.jsonl")
a = ap.parse_args()
MANIFEST = "manifest/manifest_full.json"
manifest = load_manifest(MANIFEST)
ids = json.load(open("configs/query_ids.json"))["ids"]
OUT = STORAGE / "out" / "ablation"

CONFIGS = {  # sort_by=None: tái lập đúng cấu hình tuần 8 (từ bản 1.0 mặc định đã sắp theo record_id)
    "E0_mac_dinh": ({"sort_by": None}, {}),
    "E1_tat_kiem_trung": ({"check_duplicates": False, "sort_by": None}, {}),
    "E2_row_group_mac_dinh": ({"row_group_mb": None, "sort_by": None}, {}),
    "E3_split_32mb": ({"sort_by": None}, {"spark.sql.files.maxPartitionBytes": "32m"}),
    "E4_snappy": ({"compression": "snappy", "sort_by": None}, {}),
    "E5_khong_nen": ({"compression": "none", "sort_by": None}, {}),
    "E6_sap_xep_record_id": ({"sort_by": "record_id"}, {}),
}


def stage_breakdown(spark):
    """Trả về thời gian B1, B2, B3 (giây)."""
    sch = staging_schemas()
    t = {}
    t0 = time.perf_counter()
    for name in ("numinamath", "proofnet", "leandojo", "leandojo_premise", "leandojo_file"):
        d = _read(spark, STAGING, name, sch[name])
        d.write.format("noop").mode("overwrite").save()
    t["B1_doc_parse_json"] = round(time.perf_counter() - t0, 3)
    for key, dup in (("B2_anh_xa_khong_kiem_trung", False), ("B3_anh_xa_co_kiem_trung", True)):
        t0 = time.perf_counter()
        good, _, _ = build_curated(spark, STAGING, manifest, "breakdown", check_duplicates=dup)
        good.write.format("noop").mode("overwrite").save()
        t[key] = round(time.perf_counter() - t0, 3)
    return t


Path("logs").mkdir(exist_ok=True)
for i in range(a.repeat):
    if not a.only or "breakdown" in a.only:
        spark = spark_session(master="local[4]", driver_memory="2g", app="mdl-breakdown")
        rid = new_run_id("breakdown")
        with Monitor() as m:
            t = stage_breakdown(spark)
        spark.stop()
        write_run(a.runs, make_run(rid, "stage_breakdown", {"scale": "full", "workers": 4, "repeat_idx": i},
                                   {**m.metrics(), **t}, "ok", "-", MANIFEST))
        print("breakdown", t, flush=True)
    for name, (kw, conf) in CONFIGS.items():
        if a.only and name not in a.only:
            continue
        spark = spark_session(master="local[4]", driver_memory="2g", app=f"mdl-{name}", extra=conf)
        out = OUT / name
        shutil.rmtree(out, ignore_errors=True)
        rid = new_run_id(name)
        status = "ok"
        try:
            with Monitor() as m:
                res = run_spark_etl(spark, STAGING, out, manifest, rid, **kw)
        except (Exception, KeyboardInterrupt) as e:
            status, res, m = f"failed: {type(e).__name__}: {str(e)[:200]}", {}, None
        spark.stop()
        metrics = {**(m.metrics() if m else {}), **res}
        if status == "ok":
            q = run_sql_queries(parquet_source((out / "math_record").as_posix()), ids, threads=4)
            metrics.update({k: v["seconds"] for k, v in q.items()})
            metrics["sql_total_s"] = round(sum(v["seconds"] for v in q.values()), 4)
        write_run(a.runs, make_run(rid, "ablation_etl", {"config": name, "scale": "full", "workers": 4,
                                                         "repeat_idx": i, **{k: str(v) for k, v in kw.items()},
                                                         **conf}, metrics, status, "-", MANIFEST))
        print(name, i, status, metrics.get("runtime_s"), metrics.get("elapsed_s"), metrics.get("bytes_out"),
              metrics.get("sql_total_s"), metrics.get("Q3_point_lookup"), flush=True)
