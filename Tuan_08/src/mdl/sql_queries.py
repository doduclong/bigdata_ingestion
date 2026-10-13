"""Bộ truy vấn kiểm tra bằng DuckDB — tương đương từng truy vấn Python trong queries.py.

`source_sql` là biểu thức FROM, ví dụ read_parquet('…/**/*.parquet', hive_partitioning=true) hoặc read_json(…).
"""
import time

import duckdb

PROV = ["source", "source_version", "raw_uri", "raw_row", "raw_sha256", "license", "source_url", "downloaded_at",
        "ingest_run_id"]

SQL = {
    "Q0_full_scan": "SELECT count(*), sum(length(coalesce(nl_solution, ''))), "
                    "sum(length(coalesce(formal_statement, ''))) FROM {t}",
    "Q1_count_by_source_split": "SELECT source, split, count(*) FROM {t} GROUP BY 1, 2 ORDER BY 1, 2",
    "Q2_olympiad_latex": "SELECT count(*), round(avg(length(nl_problem)), 2) FROM {t} "
                         "WHERE source = 'numinamath' AND subset = 'olympiads' AND has_latex",
    "Q3_point_lookup": "SELECT record_id, source, content_sha256 FROM {t} WHERE record_id IN ({ids}) ORDER BY 1",
    "Q4_top_premises": "SELECT p, count(*) AS c FROM (SELECT unnest(premises) AS p FROM {t} "
                       "WHERE source = 'leandojo') GROUP BY p ORDER BY c DESC, p LIMIT 10",
    "Q5_provenance_audit": "SELECT source, license, (" + " AND ".join(f"{c} IS NOT NULL" for c in PROV) +
                           ") AS ok, count(*) FROM {t} GROUP BY ALL ORDER BY 1, 2, 3",
}


def parquet_source(path, hive=True):
    return f"read_parquet('{path}/**/*.parquet', hive_partitioning={'true' if hive else 'false'})"


def jsonl_source(path):
    from .schema import FIELDS
    duck = {"string": "VARCHAR", "int": "BIGINT", "bool": "BOOLEAN", "list<string>": "VARCHAR[]"}
    cols = ", ".join(f"{n}: '{duck[t]}'" for n, t, *_ in FIELDS)
    return (f"read_json('{path}', format='newline_delimited', columns={{{cols}}}, "
            f"maximum_object_size=67108864)")


def run_sql_queries(source_sql, ids, threads=None):
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")  # giới hạn RAM của nhóm (tổng < 4 GB)
    if threads:
        con.execute(f"SET threads={threads}")
    id_list = ", ".join(f"'{i}'" for i in ids) or "NULL"
    out = {}
    for name, q in SQL.items():
        sql = q.format(t=source_sql, ids=id_list)
        t0 = time.perf_counter()
        rows = con.execute(sql).fetchall()
        out[name] = {"seconds": round(time.perf_counter() - t0, 4), "rows": len(rows),
                     "result": [list(r) for r in rows]}
    con.close()
    return out
