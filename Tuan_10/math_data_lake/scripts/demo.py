"""Demo end-to-end trên dữ liệu mẫu (không cần dữ liệu đầy đủ, ~1–2 phút, Spark local[2], 2 GB).

  1. raw mẫu (3 nguồn, 3 định dạng) -> staging JSONL
  2. nạp kho: v0 ban đầu, v1 batch mới, v2 nạp lại (idempotent)
  3. catalog + truy vấn mẫu cho các nhóm khác
  4. truy vết provenance một bản ghi mỗi nguồn về tệp raw
Chạy: python scripts/demo.py
"""
import json
import shutil
import time
from pathlib import Path

import duckdb

import _path  # noqa: F401
from mdl.catalog import build_catalog, catalog_markdown
from mdl.config import STORAGE
from mdl.lake import ingest_batch
from mdl.manifest import load_manifest
from mdl.provenance import trace
from mdl.spark_etl import spark_session
from mdl.staging import build_staging

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / "data_sample"
WORK = STORAGE / "demo"
T0 = time.perf_counter()


def step(title):
    print(f"\n{'=' * 78}\n[{time.perf_counter() - T0:6.1f}s] {title}\n{'=' * 78}")


shutil.rmtree(WORK, ignore_errors=True)
step("1. Raw mẫu -> staging JSONL (chuẩn hóa NFC, con trỏ raw)")
stats = build_staging(DS / "raw", WORK / "staging", log=lambda *_: None)
for k, v in stats.items():
    print(f"  {k:18s} {v}")
init, batch = WORK / "init", WORK / "batch"
for p in (WORK / "staging").rglob("*.jsonl"):
    d = (batch if p.name.startswith("part-train-0000") and "numinamath" in str(p) else init) / p.relative_to(
        WORK / "staging")
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(p, d)

step("2. Nạp kho Parquet: v0 ban đầu -> v1 batch NuminaMath mới -> v2 nạp lại cùng batch")
manifest = load_manifest(DS / "manifest_sample.json")
spark = spark_session(master="local[2]", driver_memory="2g", app="mdl-demo")
lake = WORK / "lake"
for stg, name in ((init, "v0 ban đầu"), (batch, "v1 batch mới"), (batch, "v2 nạp lại (idempotent)")):
    e = ingest_batch(spark, stg, lake, manifest, f"demo-{name.split()[0]}", name)
    agg = {k: sum(p[k] for p in e["partitions"].values()) for k in ("new", "unchanged", "conflict")}
    print(f"  {name:26s} mới={agg['new']:4d}  không đổi={agg['unchanged']:4d}  xung đột={agg['conflict']}  "
          f"tệp thêm={e['files_added']}  ({e['total_s']} s)")
spark.stop()

step("3. Catalog (trích) và truy vấn cho các nhóm khác")
cat = build_catalog(lake, DS / "manifest_sample.json")
print("\n".join(catalog_markdown(cat).splitlines()[:20]))
con = duckdb.connect()
con.execute(f"CREATE VIEW math_record AS SELECT * FROM read_parquet('{(lake / 'math_record').as_posix()}/**/*.parquet',"
            " hive_partitioning=true)")
print("\n-- Nhóm 3/4 (truy hồi premise): định lý Lean 4 nhiều premise nhất")
print(con.sql("SELECT lean_full_name, len(premises) AS n_premise, substr(formal_statement, 1, 60) AS stmt "
              "FROM math_record WHERE source='leandojo' ORDER BY n_premise DESC, lean_full_name LIMIT 3"))
print("-- Nhóm 5 (autoformalization): cặp NL–Lean 3 của ProofNet")
print(con.sql("SELECT subset, substr(nl_problem, 1, 50) AS nl, substr(formal_statement, 1, 40) AS lean "
              "FROM math_record WHERE source='proofnet' ORDER BY record_id LIMIT 3"))
print("-- Nhóm 2 (chất lượng): cờ cảnh báo theo nguồn")
print(con.sql("SELECT source, f, count(*) n FROM (SELECT source, unnest(quality_flags) f FROM math_record) "
              "GROUP BY ALL ORDER BY ALL"))

step("4. Truy vết provenance: record_id -> đúng bản ghi trong tệp raw (kiểm nội dung)")
ids = [r[0] for r in con.execute("SELECT min(record_id) FROM math_record GROUP BY source ORDER BY source").fetchall()]
for t in trace(lake / "math_record", DS, manifest, ids):
    print(f"  {t['record_id']} {t['source']:10s} {t['raw_uri']}#{t['raw_row']:<7d} license={t['license']:10s} "
          f"trường khớp={t['fields_checked']} lệch={t['fields_mismatch']}")
step(f"Xong. Kho demo: {lake}")
