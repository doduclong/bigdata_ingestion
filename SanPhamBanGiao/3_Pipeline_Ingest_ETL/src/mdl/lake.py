"""Kho curated có nhật ký nạp (_lake_log) và cập nhật gia tăng theo batch.

Quy tắc khi nạp một batch vào partition (source, source_version):
- record_id chưa có                    -> thêm mới (append tệp mới vào partition)
- record_id đã có, content_sha256 trùng -> bỏ qua (idempotent)
- record_id đã có, content_sha256 khác  -> KHÔNG ghi đè; đưa vào bảng lỗi với E07_CONTENT_CONFLICT
  (một source_version là bất biến; nội dung đổi phải đến dưới source_version mới => partition mới)
Thứ tự an toàn: ETL batch ra thư mục tạm -> chuyển tệp vào partition -> ghi mục nhật ký cuối cùng.
"""
import datetime as dt
import json
import shutil
import time
import uuid
from pathlib import Path

from .spark_etl import run_spark_etl
from .storage import compact

LOG_DIR = "_lake_log"


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_log(lake):
    d = Path(lake) / LOG_DIR
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))] if d.exists() else []


def _append_log(lake, entry):
    d = Path(lake) / LOG_DIR
    d.mkdir(parents=True, exist_ok=True)
    n = len(list(d.glob("*.json")))
    tmp = d / f".{n:06d}.json.tmp"
    tmp.write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.rename(d / f"{n:06d}.json")  # rename là nguyên tử trên cùng ổ đĩa


def new_run_id():
    return f"ingest-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _move_files(src_dir, dst_dir, prefix):
    dst_dir.mkdir(parents=True, exist_ok=True)
    moved = []
    for f in sorted(src_dir.glob("*.parquet")):
        target = dst_dir / f"{prefix}-{f.name}"
        f.rename(target)
        moved.append(target.name)
    return moved


def ingest_batch(spark, staging_root, lake, manifest_entries, run_id, batch_name, run_compaction=True):
    """Nạp một batch staging vào kho `lake`. Trả về mục nhật ký (đã ghi vào _lake_log)."""
    from pyspark.sql import functions as F
    lake = Path(lake)
    tmp = lake / f"_tmp_{run_id}"
    t0 = time.perf_counter()
    etl = run_spark_etl(spark, staging_root, tmp, manifest_entries, run_id)  # một lượt đọc staging
    t_etl = time.perf_counter() - t0
    stats, files_added = {}, 0
    for bdir in sorted((tmp / "math_record").glob("source=*/source_version=*")):
        src, ver = bdir.parent.name.split("=", 1)[1], bdir.name.split("=", 1)[1]
        pdir = lake / "math_record" / bdir.parent.name / bdir.name
        batch = spark.read.parquet(str(bdir))
        n_batch = batch.count()
        if pdir.exists() and any(pdir.glob("*.parquet")):
            old = spark.read.parquet(str(pdir)).select("record_id", F.col("content_sha256").alias("_old_sha"))
            j = batch.join(old, "record_id", "left")
            new = j.where(F.col("_old_sha").isNull()).drop("_old_sha")
            conflict = j.where(F.col("_old_sha").isNotNull() & (F.col("_old_sha") != F.col("content_sha256")))
            n_conf = conflict.count()
            if n_conf:
                (conflict.select("record_id", F.lit(src).alias("source"), "raw_uri", "raw_row",
                                 F.array(F.lit("E07_CONTENT_CONFLICT")).alias("errors"))
                 .write.mode("append").json(str(lake / "errors")))
            sel = tmp / "_new" / bdir.parent.name / bdir.name
            new.write.option("parquet.block.size", 16 * 2**20).parquet(str(sel))
            n_new = spark.read.parquet(str(sel)).count()
            moved = _move_files(sel, pdir, run_id) if n_new else []
        else:  # partition mới: chuyển nguyên tệp, không cần ghi lại
            n_new, n_conf = n_batch, 0
            moved = _move_files(bdir, pdir, run_id)
        stats[f"{src}/{ver}"] = {"batch": n_batch, "new": n_new, "unchanged": n_batch - n_new - n_conf,
                                 "conflict": n_conf, "files_added": len(moved)}
        files_added += len(moved)
    if (tmp / "errors").exists():
        for f in (tmp / "errors").glob("*.json"):
            if f.stat().st_size:
                (lake / "errors").mkdir(parents=True, exist_ok=True)
                f.rename(lake / "errors" / f"{run_id}-{f.name}")
    shutil.rmtree(tmp, ignore_errors=True)
    t_ingest = time.perf_counter() - t0
    comp = compact(spark, lake / "math_record", small_mb=32) if run_compaction and files_added else None
    entry = {"version": len(read_log(lake)), "run_id": run_id, "batch": batch_name, "committed_at": _now(),
             "operation": "append", "staging": str(staging_root), "partitions": stats, "files_added": files_added,
             "records_error": etl["records_error"], "read_errors": etl["read_errors"],
             "etl_s": round(t_etl, 3), "ingest_s": round(t_ingest, 3), "compaction": comp,
             "total_s": round(time.perf_counter() - t0, 3)}
    _append_log(lake, entry)
    return entry
