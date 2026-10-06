"""Sinh catalog (JSON + Markdown) cho kho tuần 6 và truy vết provenance 10 bản ghi/nguồn về tệp raw.

Chạy sau scripts/chay_gia_tang.py:  python scripts/tao_catalog.py
"""
import json
from pathlib import Path

import duckdb

import _path  # noqa: F401
from mdl.catalog import build_catalog, catalog_markdown
from mdl.config import STORAGE
from mdl.manifest import load_manifest
from mdl.provenance import trace

MANIFEST_PATH = "manifest/manifest_full.json"
manifest = load_manifest(MANIFEST_PATH)
LAKE = STORAGE / "lake_w6"

# Catalog và truy vết provenance trên kho cuối cùng
cat = build_catalog(LAKE, MANIFEST_PATH)
Path("catalog").mkdir(exist_ok=True)
Path("catalog/catalog.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
Path("catalog/catalog.md").write_text(catalog_markdown(cat), encoding="utf-8")
con = duckdb.connect()
ids = [r[0] for r in con.execute(f"""SELECT record_id FROM (SELECT record_id, source, row_number() OVER
    (PARTITION BY source ORDER BY md5(record_id || 'trace')) rn FROM read_parquet(
    '{(LAKE / 'math_record').as_posix()}/**/*.parquet', hive_partitioning=true)) WHERE rn <= 10""").fetchall()]
tr = trace(LAKE / "math_record", STORAGE, manifest, ids)
Path("results/raw/provenance_trace.json").write_text(json.dumps(
    {"checked": len(tr), "ok": sum(t["ok"] for t in tr), "results": tr}, ensure_ascii=False, indent=1),
    encoding="utf-8")
print("provenance trace:", sum(t["ok"] for t in tr), "/", len(tr))
