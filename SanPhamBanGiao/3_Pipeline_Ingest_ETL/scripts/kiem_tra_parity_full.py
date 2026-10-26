"""So khớp đầu ra baseline (JSONL) và Spark (Parquet) trên toàn bộ dữ liệu, từng bản ghi, mọi cột nội dung.

Chạy sau chay_baseline.py --scales full và chay_spark.py --scales full.
DuckDB bị giới hạn 2 GB RAM, 4 luồng.  Kết quả: results/raw/parity_full.json
"""
import json
import time
from pathlib import Path

import duckdb

import _path  # noqa: F401
from mdl.config import STORAGE
from mdl.schema import FIELDS

SKIP = {"ingest_run_id"}  # phụ thuộc lần chạy
cols = [n for n, *_ in FIELDS if n not in SKIP]
base = STORAGE / "out" / "baseline" / "full" / "math_record.jsonl"
spark = STORAGE / "out" / "spark" / "full" / "math_record"


def row_hash(alias):
    parts = ", ".join(f"coalesce(CAST({alias}.{c} AS VARCHAR), '<null>')" for c in cols)
    return f"md5(concat_ws('\u001f', {parts}))"


con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET threads=4; SET preserve_insertion_order=false")
con.execute(f"SET temp_directory='{(STORAGE / 'duckdb_tmp').as_posix()}'")
t0 = time.perf_counter()
types = ", ".join(f"{n}: '{ {'string': 'VARCHAR', 'int': 'BIGINT', 'bool': 'BOOLEAN', 'list<string>': 'VARCHAR[]'}[t] }'"
                  for n, t, *_ in FIELDS)
con.execute(f"""CREATE TABLE b AS SELECT record_id, source, {row_hash('j')} AS h FROM
    read_json('{base.as_posix()}', format='newline_delimited', columns={{{types}}}, maximum_object_size=67108864) j""")
con.execute(f"""CREATE TABLE s AS SELECT record_id, source, {row_hash('p')} AS h FROM
    read_parquet('{spark.as_posix()}/**/*.parquet', hive_partitioning=true) p""")
res = {
    "baseline_rows": con.execute("SELECT count(*) FROM b").fetchone()[0],
    "spark_rows": con.execute("SELECT count(*) FROM s").fetchone()[0],
    "only_in_baseline": con.execute("SELECT count(*) FROM b ANTI JOIN s USING (record_id)").fetchone()[0],
    "only_in_spark": con.execute("SELECT count(*) FROM s ANTI JOIN b USING (record_id)").fetchone()[0],
    "hash_mismatch": con.execute("SELECT count(*) FROM b JOIN s USING (record_id) WHERE b.h <> s.h").fetchone()[0],
    "mismatch_by_source": con.execute("SELECT b.source, count(*) FROM b JOIN s USING (record_id) "
                                      "WHERE b.h <> s.h GROUP BY 1").fetchall(),
    "columns_compared": cols,
}
res["seconds"] = round(time.perf_counter() - t0, 1)
Path("results/raw").mkdir(parents=True, exist_ok=True)
Path("results/raw/parity_full.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print({k: v for k, v in res.items() if k != "columns_compared"})
