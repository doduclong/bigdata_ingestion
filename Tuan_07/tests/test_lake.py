"""Kiểm thử nạp gia tăng, idempotent, xung đột nội dung, nhật ký kho, catalog và truy vết provenance (trên mẫu)."""
import json
import shutil

from mdl.catalog import build_catalog, catalog_markdown
from mdl.lake import ingest_batch, read_log
from mdl.provenance import trace
from mdl.spark_etl import run_spark_etl

from conftest import ROOT, SAMPLE_MANIFEST

BATCH_FILE = "part-train-00000-of-00005.jsonl"  # shard NuminaMath trong bản mẫu (477 bản ghi)


def _split(staging, tmp):
    init, batch = tmp / "init", tmp / "batch"
    for p in staging.rglob("*.jsonl"):
        d = (batch if p.name == BATCH_FILE else init) / p.relative_to(staging)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(p, d)
    return init, batch


def _keys(spark, path):
    return sorted((r[0], r[1]) for r in spark.read.parquet(str(path)).select("record_id", "content_sha256").collect())


def _agg(entry, k):
    return sum(p[k] for p in entry["partitions"].values())


def test_incremental_equals_full_and_is_idempotent(spark, staging_sample, manifest, tmp_path):
    init, batch = _split(staging_sample, tmp_path)
    lake = tmp_path / "lake"
    v0 = ingest_batch(spark, init, lake, manifest, "r0", "v0")
    v1 = ingest_batch(spark, batch, lake, manifest, "r1", "v1")
    v2 = ingest_batch(spark, batch, lake, manifest, "r2", "v2")
    assert _agg(v0, "new") == 520 and _agg(v1, "new") == 477
    assert _agg(v2, "new") == 0 and _agg(v2, "unchanged") == 477 and v2["files_added"] == 0
    run_spark_etl(spark, staging_sample, tmp_path / "full", manifest, "full")
    assert _keys(spark, lake / "math_record") == _keys(spark, tmp_path / "full" / "math_record")
    assert [e["version"] for e in read_log(lake)] == [0, 1, 2]


def test_content_conflict_is_quarantined(spark, staging_sample, manifest, tmp_path):
    init, batch = _split(staging_sample, tmp_path)
    lake = tmp_path / "lake"
    ingest_batch(spark, staging_sample, lake, manifest, "r0", "all")
    f = next(batch.rglob(BATCH_FILE))
    lines = f.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[0])
    rec["solution"] = rec["solution"] + " (đã sửa)"
    f.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    before = _keys(spark, lake / "math_record")
    v = ingest_batch(spark, batch, lake, manifest, "r1", "sửa nội dung cùng phiên bản")
    assert _agg(v, "conflict") == 1 and _agg(v, "new") == 0
    assert _keys(spark, lake / "math_record") == before  # không ghi đè
    errs = [json.loads(l) for p in (lake / "errors").glob("*.json") for l in open(p, encoding="utf-8")]
    assert any("E07_CONTENT_CONFLICT" in e["errors"] for e in errs)


def test_catalog_and_provenance_trace(spark, staging_sample, manifest, tmp_path):
    lake = tmp_path / "lake"
    ingest_batch(spark, staging_sample, lake, manifest, "r0", "all")
    cat = build_catalog(lake, SAMPLE_MANIFEST)
    t = cat["tables"][0]
    assert t["rows"] == 997 and {p["source"] for p in t["partitions"]} == {"numinamath", "proofnet", "leandojo"}
    assert "| numinamath |" in catalog_markdown(cat)
    ids = [r[0] for r in spark.read.parquet(str(lake / "math_record")).select("record_id").limit(500).collect()][::25]
    res = trace(lake / "math_record", ROOT / "data_sample", manifest, ids)
    assert len(res) == len(ids)
    assert all(r["fields_mismatch"] == [] for r in res), [r for r in res if r["fields_mismatch"]]
