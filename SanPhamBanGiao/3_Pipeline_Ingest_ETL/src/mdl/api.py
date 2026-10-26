"""API dữ liệu cho các nhóm khác (FastAPI + DuckDB đọc trực tiếp kho Parquet).

Chạy:  python scripts/mdl.py serve [--port 8000]      Tài liệu tương tác: http://localhost:8000/docs
Mọi tham số được kiểm tra miền giá trị và truyền dạng tham số SQL (không ghép chuỗi).
"""
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Literal, Optional

import duckdb
import pyarrow.parquet as pq
from fastapi import FastAPI, HTTPException, Query
from fastapi import Path as PathParam
from fastapi.responses import FileResponse

from .config import PIPELINE_VERSION, SCHEMA_VERSION, STORAGE
from .schema import FIELD_NAMES

LAKE = Path(os.environ.get("MDL_LAKE", STORAGE / "lake"))
MANIFEST = Path(os.environ.get("MDL_MANIFEST", Path(__file__).resolve().parents[2] / "manifest" / "manifest_full.json"))
RAW_ROOT = Path(os.environ.get("MDL_RAW_ROOT", STORAGE))
ID_PATTERN = r"^[0-9a-f]{20}$"
Source = Literal["numinamath", "proofnet", "leandojo"]
LIGHT = ["record_id", "source", "source_version", "record_type", "split", "subset", "nl_problem", "formal_language",
         "formal_statement", "lean_full_name", "num_tactics", "has_latex", "has_lean", "quality_flags"]

app = FastAPI(title="Math Data Lake API", version=PIPELINE_VERSION,
              description="Truy cập kho math_record (NuminaMath-CoT, ProofNet, LeanDojo Benchmark 4) của Nhóm 1.")
_con = None
_lock = threading.Lock()
_catalog = None


def con():
    """Một kết nối DuckDB dùng chung; mỗi request dùng cursor riêng (an toàn đa luồng)."""
    global _con
    with _lock:
        if _con is None:
            _con = duckdb.connect()
            _con.execute("SET memory_limit='1GB'; SET threads=4")
            _con.execute(f"CREATE VIEW math_record AS SELECT * FROM read_parquet("
                         f"'{(LAKE / 'math_record').as_posix()}/**/*.parquet', hive_partitioning=true)")
    return _con.cursor()


def _rows(cur, sql, params=()):
    res = cur.execute(sql, list(params))
    cols = [d[0] for d in res.description]
    return [dict(zip(cols, r)) for r in res.fetchall()]


def _fields(fields):
    if not fields:
        return LIGHT
    out = [f.strip() for f in fields.split(",") if f.strip()]
    bad = [f for f in out if f not in FIELD_NAMES]
    if bad:
        raise HTTPException(400, f"cột không tồn tại: {bad}")
    return out


def _where(source, split, subset, has_lean, record_type):
    cond, params = [], []
    for col, val in (("source", source), ("split", split), ("subset", subset), ("record_type", record_type)):
        if val is not None:
            cond.append(f"{col} = ?")
            params.append(val)
    if has_lean is not None:
        cond.append("has_lean = ?")
        params.append(has_lean)
    return (" WHERE " + " AND ".join(cond)) if cond else "", params


@app.get("/health")
def health():
    t0 = time.perf_counter()
    n = con().execute("SELECT count(*) FROM math_record").fetchone()[0]
    return {"status": "ok", "records": n, "lake": str(LAKE), "schema_version": SCHEMA_VERSION,
            "pipeline_version": PIPELINE_VERSION, "ms": round(1000 * (time.perf_counter() - t0), 1)}


@app.get("/stats")
def stats():
    return _rows(con(), "SELECT source, source_version, split, count(*) AS records, sum(has_latex::INT) AS with_latex, "
                        "sum(has_lean::INT) AS with_lean FROM math_record GROUP BY ALL ORDER BY ALL")


@app.get("/records/{record_id}")
def get_record(record_id: str = PathParam(..., pattern=ID_PATTERN)):
    rows = _rows(con(), "SELECT * FROM math_record WHERE record_id = ?", [record_id])
    if not rows:
        raise HTTPException(404, "không có record_id này")
    return rows[0]


@app.get("/records")
def list_records(source: Optional[Source] = None, split: Optional[str] = Query(None, max_length=20),
                 subset: Optional[str] = Query(None, max_length=80), has_lean: Optional[bool] = None,
                 record_type: Optional[Literal["problem_solution", "nl_formal_pair", "formal_theorem"]] = None,
                 fields: Optional[str] = None, limit: int = Query(100, ge=1, le=1000),
                 after: Optional[str] = Query(None, pattern=ID_PATTERN)):
    """Phân trang theo khóa: truyền `after` = record_id cuối của trang trước (ổn định, không lệch khi dữ liệu lớn)."""
    cols = _fields(fields)
    where, params = _where(source, split, subset, has_lean, record_type)
    if after:
        where += (" AND " if where else " WHERE ") + "record_id > ?"
        params.append(after)
    rows = _rows(con(), f"SELECT {', '.join(cols)} FROM math_record{where} ORDER BY record_id LIMIT ?",
                 params + [limit])
    return {"count": len(rows), "next_after": rows[-1]["record_id"] if len(rows) == limit and "record_id" in cols
            else None, "records": rows}


@app.get("/premises/{premise}/theorems")
def theorems_using_premise(premise: str = PathParam(..., max_length=300), limit: int = Query(50, ge=1, le=1000)):
    """Nhóm 3/4: định lý LeanDojo có dùng premise này trong chứng minh."""
    return _rows(con(), "SELECT record_id, lean_full_name, lean_file_path, split, formal_statement FROM math_record "
                        "WHERE source = 'leandojo' AND list_contains(premises, ?) ORDER BY record_id LIMIT ?",
                 [premise, limit])


@app.get("/pairs/nl-formal")
def nl_formal_pairs(split: Optional[Literal["valid", "test"]] = None):
    """Nhóm 5/6: cặp phát biểu NL – Lean 3 của ProofNet."""
    where = " AND split = ?" if split else ""
    return _rows(con(), "SELECT record_id, source_record_key, split, subset, nl_problem, nl_solution, formal_language, "
                        f"formal_statement, formal_header FROM math_record WHERE source = 'proofnet'{where} "
                        "ORDER BY record_id", [split] if split else [])


@app.get("/provenance/{record_id}")
def provenance(record_id: str = PathParam(..., pattern=ID_PATTERN)):
    """Truy vết bản ghi về đúng dòng trong tệp raw, kiểm sha256 theo manifest."""
    from .manifest import load_manifest
    from .provenance import trace
    res = trace(LAKE / "math_record", RAW_ROOT, load_manifest(MANIFEST), [record_id])
    if not res:
        raise HTTPException(404, "không có record_id này")
    return res[0]


@app.get("/catalog")
def catalog():
    global _catalog
    if _catalog is None:
        from .catalog import build_catalog
        _catalog = build_catalog(LAKE, MANIFEST)
    return _catalog


@app.get("/export")
def export(source: Source, split: Optional[str] = Query(None, max_length=20), fields: Optional[str] = None,
           fmt: Literal["parquet", "jsonl"] = "parquet"):
    """Xuất một lát dữ liệu theo nguồn/split. Ghi theo record batch ra tệp tạm => RAM không phụ thuộc kích thước."""
    cols = _fields(fields) if fields else FIELD_NAMES
    where, params = _where(source, split, None, None, None)
    reader = con().execute(f"SELECT {', '.join(cols)} FROM math_record{where} ORDER BY record_id",
                           params).fetch_record_batch(50_000)
    tmp_dir = STORAGE / "api_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=f".{fmt}", dir=tmp_dir)
    os.close(fd)
    if fmt == "parquet":
        with pq.ParquetWriter(path, reader.schema, compression="zstd") as w:
            for batch in reader:
                w.write_batch(batch)
    else:
        import json
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for batch in reader:
                for r in batch.to_pylist():
                    f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    name = f"math_record_{source}_{split or 'all'}.{fmt}"
    return FileResponse(path, filename=name, background=_cleanup(path))


def _cleanup(path):
    from starlette.background import BackgroundTask
    return BackgroundTask(lambda: Path(path).unlink(missing_ok=True))
