"""CLI thống nhất của Math Data Lake.  Chạy từ thư mục gốc dự án:  python -m mdl <lệnh> [tùy chọn]
(đặt PYTHONPATH=src hoặc dùng scripts/mdl.py).

  sample              tái tạo data_sample/curated từ data_sample/raw (không cần dữ liệu đầy đủ)
  download            tải snapshot ghim phiên bản + manifest + checksum
  verify              kiểm tra checksum vùng raw theo manifest
  staging             raw -> staging JSONL
  etl                 Spark ETL staging -> kho Parquet (dựng lại toàn bộ)
  ingest STAGING      nạp gia tăng một batch staging vào kho
  catalog             sinh catalog (JSON + Markdown) cho kho
  trace ID [ID...]    truy vết provenance các record_id về tệp raw
  query "SQL"         chạy SQL DuckDB; bảng `math_record` trỏ tới kho
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _lake(args):
    from .config import STORAGE
    return Path(args.lake) if args.lake else STORAGE / "lake"


def cmd_sample(args):
    import shutil

    import pyarrow as pa
    import pyarrow.parquet as pq

    from .manifest import load_manifest
    from .readers import dumps
    from .schema import FIELD_NAMES, arrow_schema
    from .staging import build_staging, iter_jsonl, load_corpus_lookups, staging_files
    from .transform import to_unified, validate
    ds = ROOT / "data_sample"
    stg, cur = ds / "staging", ds / "curated"
    shutil.rmtree(stg, ignore_errors=True)
    build_staging(ds / "raw", stg, log=lambda *_: None)
    code, imports = load_corpus_lookups(stg)
    ctx = {"manifest": load_manifest(ds / "manifest_sample.json"), "premise_code": code, "file_imports": imports,
           "run_id": "sample"}
    recs, errs = [], 0
    for src in ("numinamath", "proofnet", "leandojo"):
        for s in iter_jsonl(staging_files(stg, src)):
            r = to_unified(s, ctx)
            if validate(r):
                errs += 1
            else:
                recs.append(r)
    cur.mkdir(parents=True, exist_ok=True)
    with open(cur / "math_record_sample.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in recs:
            f.write(dumps({k: r[k] for k in FIELD_NAMES}) + "\n")
    pq.write_table(pa.Table.from_pylist(recs, schema=arrow_schema()), cur / "math_record_sample.parquet")
    shutil.rmtree(stg, ignore_errors=True)
    print(f"{len(recs)} bản ghi -> {cur}  (lỗi: {errs})")


def cmd_download(args):
    from .config import RAW
    from .manifest import build_manifest, fetch_all
    fetch_all(RAW)
    m = build_manifest(RAW, ROOT / "manifest" / "manifest_full.json")
    print(len(m["files"]), "tệp")


def cmd_verify(args):
    from .config import RAW
    from .manifest import verify
    bad = verify(RAW, ROOT / "manifest" / "manifest_full.json")
    print("OK" if not bad else bad)
    return 1 if bad else 0


def cmd_staging(args):
    from .config import RAW, STAGING
    from .staging import build_staging
    print(build_staging(RAW, STAGING))


def _spark(args):
    from .spark_etl import spark_session
    return spark_session(master=f"local[{args.cores}]", driver_memory="2g")


def cmd_etl(args):
    from .config import STAGING
    from .manifest import load_manifest
    from .spark_etl import run_spark_etl
    spark = _spark(args)
    res = run_spark_etl(spark, args.staging or STAGING, _lake(args), load_manifest(ROOT / "manifest" /
                                                                                   "manifest_full.json"), "cli-etl")
    spark.stop()
    print(json.dumps({k: v for k, v in res.items() if k != "quality_flags"}, ensure_ascii=False))


def cmd_ingest(args):
    from .lake import ingest_batch, new_run_id
    from .manifest import load_manifest
    spark = _spark(args)
    e = ingest_batch(spark, args.staging, _lake(args), load_manifest(ROOT / "manifest" / "manifest_full.json"),
                     new_run_id(), args.name or str(args.staging))
    spark.stop()
    print(json.dumps(e, ensure_ascii=False, indent=1))


def cmd_catalog(args):
    from .catalog import build_catalog, catalog_markdown
    cat = build_catalog(_lake(args), ROOT / "manifest" / "manifest_full.json")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "catalog.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out / "catalog.md").write_text(catalog_markdown(cat), encoding="utf-8")
    print(out / "catalog.md")


def cmd_trace(args):
    from .config import STORAGE
    from .manifest import load_manifest
    from .provenance import trace
    res = trace(_lake(args) / "math_record", STORAGE, load_manifest(ROOT / "manifest" / "manifest_full.json"),
                args.ids)
    print(json.dumps(res, ensure_ascii=False, indent=1))


def cmd_query(args):
    import duckdb
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'; SET threads=4")
    con.execute(f"CREATE VIEW math_record AS SELECT * FROM read_parquet("
                f"'{(_lake(args) / 'math_record').as_posix()}/**/*.parquet', hive_partitioning=true)")
    print(con.sql(args.sql))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mdl", description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--lake", default=None, help="thư mục kho (mặc định <storage>/lake)")
    ap.add_argument("--cores", type=int, default=4)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("sample", "download", "verify", "staging"):
        sub.add_parser(name)
    p = sub.add_parser("etl")
    p.add_argument("--staging", default=None)
    p = sub.add_parser("ingest")
    p.add_argument("staging")
    p.add_argument("--name", default=None)
    p = sub.add_parser("catalog")
    p.add_argument("--out", default="docs/catalog")
    p = sub.add_parser("trace")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("query")
    p.add_argument("sql")
    args = ap.parse_args(argv)
    return globals()[f"cmd_{args.cmd}"](args) or 0


if __name__ == "__main__":
    sys.exit(main())
