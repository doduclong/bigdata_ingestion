"""Kiểm thử bố trí lưu trữ: compaction giảm số tệp mà không làm mất/thay đổi dữ liệu; truy vấn SQL = Python."""
import json

from mdl.queries import QUERIES
from mdl.spark_etl import run_spark_etl
from mdl.sql_queries import parquet_source, run_sql_queries
from mdl.storage import compact, dir_stats


def _content(spark, path):
    return sorted((r["record_id"], r["content_sha256"]) for r in
                  spark.read.parquet(str(path)).select("record_id", "content_sha256").collect())


def test_compaction_preserves_data(spark, staging_sample, manifest, tmp_path):
    out = tmp_path / "small"
    run_spark_etl(spark, staging_sample, out, manifest, "small", max_records_per_file=20, repartition=8)
    table = out / "math_record"
    before = dir_stats(table)
    data_before = _content(spark, table)
    assert before["files"] >= 997 // 20  # nhiều tệp nhỏ
    res = compact(spark, table, target_mb=128)
    after = dir_stats(table)
    assert after["files"] == 3  # mỗi partition source/source_version còn đúng 1 tệp
    assert res["files_before"] == before["files"] and res["files_after"] == 3
    assert _content(spark, table) == data_before
    assert not list(table.rglob("*.compacting")) and not list(table.rglob("*.old"))


def test_sql_queries_match_python(spark, staging_sample, manifest, tmp_path, python_records):
    out = tmp_path / "q"
    run_spark_etl(spark, staging_sample, out, manifest, "q")
    ids = [r["record_id"] for r in python_records[:5]] + ["0" * 20]
    jsonl = tmp_path / "records.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in python_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    sql = run_sql_queries(parquet_source((out / "math_record").as_posix()), ids, threads=2)
    for name, fn in QUERIES.items():
        py = fn(jsonl, ids=ids)
        got = [tuple(x) for x in sql[name]["result"]]
        if name == "Q5_provenance_audit":  # ingest_run_id khác nhau giữa hai đường nhưng đều khác null
            py = [(s, lic, ok, n) for s, lic, ok, n in py]
        assert got == [tuple(x) for x in py], name
