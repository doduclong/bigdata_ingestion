"""Sinh catalog cho kho curated: bảng, cột, partition, nguồn/giấy phép/phiên bản, lịch sử nạp, chất lượng, truy vấn mẫu."""
import datetime as dt
import json
from pathlib import Path

import duckdb

from .config import PIPELINE_VERSION, SCHEMA_VERSION, SOURCES
from .lake import read_log
from .schema import FIELDS, PARTITION_COLS
from .sql_queries import SQL

EXAMPLES = {
    "Đếm bản ghi theo nguồn và split": "SELECT source, split, count(*) FROM math_record GROUP BY ALL ORDER BY ALL",
    "Cặp NL–Lean 3 của ProofNet theo sách": "SELECT subset, count(*) FROM math_record WHERE source = 'proofnet' "
                                            "GROUP BY 1 ORDER BY 2 DESC",
    "Định lý Lean 4 dùng một premise cho trước": "SELECT lean_full_name, formal_statement FROM math_record "
                                                  "WHERE source = 'leandojo' AND list_contains(premises, 'Nat.succ_le_iff')",
    "Truy ngược nguồn gốc một bản ghi": "SELECT raw_uri, raw_row, raw_sha256, license, downloaded_at, ingest_run_id "
                                        "FROM math_record WHERE record_id = '<id>'",
    "Bài olympiad có LaTeX cho Nhóm 8": "SELECT record_id, nl_problem FROM math_record "
                                        "WHERE source = 'numinamath' AND subset = 'olympiads' AND has_latex LIMIT 10",
}


def build_catalog(lake, manifest_path):
    lake = Path(lake)
    table = lake / "math_record"
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'; SET threads=4")
    src = f"read_parquet('{table.as_posix()}/**/*.parquet', hive_partitioning=true)"
    parts = []
    for d in sorted(table.glob("source=*/source_version=*")):
        files = list(d.glob("*.parquet"))
        s, v = d.parent.name.split("=", 1)[1], d.name.split("=", 1)[1]
        n, splits, licenses, urls = con.execute(f"SELECT count(*), string_agg(DISTINCT split, ',' ORDER BY split), "
                                "string_agg(DISTINCT license, ',' ORDER BY license), "
                                "string_agg(DISTINCT source_url, ',' ORDER BY source_url) FROM read_parquet("
                                f"'{d.as_posix()}/*.parquet')").fetchone()
        parts.append({"source": s, "source_version": v, "path": str(d.relative_to(lake)).replace("\\", "/"),
                      "rows": n, "splits": splits, "files": len(files),
                      "bytes": sum(p.stat().st_size for p in files), "license": licenses,
                      "source_url": urls})
    flags = con.execute(f"SELECT source, f, count(*) FROM (SELECT source, unnest(quality_flags) f FROM {src}) "
                        "GROUP BY ALL ORDER BY ALL").fetchall()
    errors = []
    if (lake / "errors").exists() and any(p.stat().st_size for p in (lake / "errors").glob("*.json")):
        errors = con.execute(f"SELECT source, e, count(*) FROM (SELECT source, unnest(errors) e FROM read_json("
                             f"'{(lake / 'errors').as_posix()}/*.json', format='newline_delimited')) "
                             "GROUP BY ALL ORDER BY ALL").fetchall()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    return {
        "catalog_version": "1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "lake": str(lake),
        "tables": [{
            "name": "math_record", "location": "math_record/", "format": "parquet (zstd, row group 16 MB)",
            "partition_columns": PARTITION_COLS, "primary_key": ["record_id", "source_version"],
            "schema_version": SCHEMA_VERSION, "pipeline_version": PIPELINE_VERSION,
            "rows": sum(p["rows"] for p in parts), "bytes": sum(p["bytes"] for p in parts),
            "columns": [{"name": n, "type": t, "nullable": nl, "description": d} for n, t, nl, d in FIELDS],
            "partitions": parts,
            "quality_flags": [{"source": s, "flag": f, "count": c} for s, f, c in flags],
            "errors": [{"source": s, "code": e, "count": c} for s, e, c in errors],
        }],
        "sources": [{"source": e["source"], "raw_uri": e["raw_uri"], "sha256": e["sha256"], "bytes": e["bytes"],
                     "license": e["license"], "version": e["source_version"], "downloaded_at": e["downloaded_at"]}
                    for e in manifest["files"]],
        "history": read_log(lake),
        "example_queries": EXAMPLES,
        "check_queries": SQL,
    }


def catalog_markdown(cat):
    t = cat["tables"][0]
    out = [f"# Catalog — kho Math Data Lake (sinh tự động lúc {cat['generated_at']})", "",
           f"Bảng `{t['name']}`: {t['rows']:,} bản ghi, {t['bytes'] / 2**20:,.1f} MB, định dạng {t['format']}, "
           f"partition `{'/'.join(t['partition_columns'])}`, khóa `{', '.join(t['primary_key'])}`, "
           f"lược đồ {t['schema_version']}, pipeline {t['pipeline_version']}.", "",
           "## Partition", "", "| Nguồn | Phiên bản | Split | Bản ghi | Tệp | MB | Giấy phép |", "|---|---|---|---|---|---|---|"]
    for p in t["partitions"]:
        out.append(f"| {p['source']} | {p['source_version']} | {p['splits']} | {p['rows']:,} | {p['files']} | "
                   f"{p['bytes'] / 2**20:,.1f} | {p['license']} |")
    out += ["", "## Lịch sử nạp (_lake_log)", "", "| v | Batch | Thời điểm (UTC) | Mới | Không đổi | Xung đột | Tệp thêm | "
            "Tổng (s) |", "|---|---|---|---|---|---|---|---|"]
    for h in cat["history"]:
        agg = {k: sum(p[k] for p in h["partitions"].values()) for k in ("new", "unchanged", "conflict")}
        out.append(f"| {h['version']} | {h['batch']} | {h['committed_at']} | {agg['new']:,} | {agg['unchanged']:,} | "
                   f"{agg['conflict']:,} | {h['files_added']} | {h['total_s']} |")
    out += ["", "## Chất lượng", "", "| Nguồn | Mã | Số bản ghi |", "|---|---|---|"]
    out += [f"| {e['source']} | {e['code']} (lỗi, ngoài kho) | {e['count']} |" for e in t["errors"]]
    out += [f"| {q['source']} | {q['flag']} (cảnh báo) | {q['count']:,} |" for q in t["quality_flags"]]
    out += ["", "## Cột", "", "| Cột | Kiểu | Null | Mô tả |", "|---|---|---|---|"]
    out += [f"| `{c['name']}` | {c['type']} | {'có' if c['nullable'] else 'không'} | "
            f"{c['description'].replace('|', '/')} |" for c in t["columns"]]
    out += ["", "## Truy vấn mẫu (DuckDB, `math_record` = read_parquet(... , hive_partitioning=true))", ""]
    for k, v in cat["example_queries"].items():
        out += [f"- **{k}:** `{v}`"]
    return "\n".join(out) + "\n"
