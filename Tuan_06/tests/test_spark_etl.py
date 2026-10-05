"""Kiểm thử Spark ETL: parity với bản Python, idempotent, xử lý dòng hỏng và khóa trùng."""
from mdl.schema import FIELD_NAMES
from mdl.spark_etl import build_curated, run_spark_etl

# Cột phụ thuộc lần chạy (không so sánh nội dung)
RUN_COLS = {"ingest_run_id"}


def _spark_rows(df):
    return {r["record_id"]: r.asDict(recursive=True) for r in df.collect()}


def test_parity_with_python_reference(spark, staging_sample, manifest, python_records):
    good, bad, bad_lines = build_curated(spark, staging_sample, manifest, "test")
    got = _spark_rows(good)
    # collect() thay vì count(): Spark cấm count() chỉ dựa trên cột _corrupt_record
    assert bad.collect() == [] and bad_lines.collect() == []
    assert set(got) == {r["record_id"] for r in python_records}
    mismatches = []
    for r in python_records:
        g = got[r["record_id"]]
        for k in FIELD_NAMES:
            if k not in RUN_COLS and g[k] != r[k]:
                mismatches.append((r["source"], r["record_id"], k, str(r[k])[:60], str(g[k])[:60]))
    assert mismatches == [], mismatches[:10]


def test_write_is_idempotent(spark, staging_sample, manifest, tmp_path):
    m1 = run_spark_etl(spark, staging_sample, tmp_path / "out", manifest, "run-1")
    m2 = run_spark_etl(spark, staging_sample, tmp_path / "out", manifest, "run-2")
    assert m1["records_out"] == m2["records_out"] == 997
    ids = spark.read.parquet(str(tmp_path / "out" / "math_record")).select("record_id", "source_version")
    assert ids.distinct().count() == ids.count() == 997
    parts = sorted(p.name for p in (tmp_path / "out" / "math_record").iterdir() if p.is_dir())
    assert parts == ["source=leandojo", "source=numinamath", "source=proofnet"]


def test_corrupt_lines_and_duplicates(spark, corrupt_staging, manifest, tmp_path):
    m = run_spark_etl(spark, corrupt_staging, tmp_path / "out", manifest, "run-bad")
    assert m["records_out"] == 997  # bản ghi tốt không bị ảnh hưởng
    assert m["read_errors"] == 2  # JSON cụt + không phải object
    errs = spark.read.json(str(tmp_path / "out" / "errors")).collect()
    codes = sorted(e for r in errs for e in r["errors"])
    assert codes == ["E03_EMPTY_CONTENT", "E06_DUPLICATE_KEY"]
