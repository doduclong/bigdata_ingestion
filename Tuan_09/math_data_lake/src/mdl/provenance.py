"""Truy vết provenance: từ record_id trong kho curated quay về đúng bản ghi trong tệp raw bất biến.

Các bước: tra (raw_uri, raw_row, raw_sha256) trong kho -> kiểm sha256 tệp raw theo manifest -> đọc đúng dòng raw
-> so khớp nội dung gốc (sau NFC) với các cột curated. Đọc mảng JSON của LeanDojo theo luồng để RAM nhỏ.
"""
import json
import unicodedata
from functools import lru_cache
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from .manifest import sha256_file


@lru_cache(maxsize=64)
def _sha(path):
    return sha256_file(path)


def _nfc(s):
    return unicodedata.normalize("NFC", s) if isinstance(s, str) else s


def iter_json_array(path, chunk=1 << 20):
    """Duyệt mảng JSON lớn từng phần tử mà không nạp cả tệp (bộ nhớ ~ một phần tử + một chunk)."""
    dec = json.JSONDecoder()
    with open(path, encoding="utf-8") as f:
        buf, pos = f.read(chunk), 0
        pos = buf.index("[") + 1
        while True:
            while True:
                while pos < len(buf) and buf[pos] in " \r\n\t,":
                    pos += 1
                if pos < len(buf):
                    break
                more = f.read(chunk)
                if not more:
                    return
                buf, pos = buf[pos:] + more, 0
            if buf[pos] == "]":
                return
            while True:
                try:
                    obj, end = dec.raw_decode(buf, pos)
                    break
                except json.JSONDecodeError:
                    more = f.read(chunk)
                    if not more:
                        raise
                    buf, pos = buf[pos:] + more, 0
            yield obj
            pos = end
            if pos > chunk:
                buf, pos = buf[pos:], 0


def read_raw_row(storage, raw_uri, raw_row):
    """Đọc bản ghi thứ `raw_row` của tệp raw. Tệp mẫu (data_sample) mang cột `_orig_row` => tìm theo cột đó."""
    p = Path(storage) / raw_uri
    if p.suffix == ".parquet":
        pf = pq.ParquetFile(p)
        if "_orig_row" in pf.schema_arrow.names:
            t = pf.read()
            for r in t.to_pylist():
                if r["_orig_row"] == raw_row:
                    return r
            raise IndexError(raw_row)
        offset = 0
        for g in range(pf.num_row_groups):
            n = pf.metadata.row_group(g).num_rows
            if raw_row < offset + n:
                return pf.read_row_group(g).slice(raw_row - offset, 1).to_pylist()[0]
            offset += n
        raise IndexError(raw_row)
    if p.suffix == ".jsonl":
        with open(p, encoding="utf-8") as f:
            for i, line in enumerate(f):
                obj = json.loads(line)
                if obj.get("_orig_row", i) == raw_row:
                    return obj
        raise IndexError(raw_row)
    for i, obj in enumerate(iter_json_array(p)):
        if obj.get("_orig_row", i) == raw_row:
            return obj
    raise IndexError(raw_row)


def _expected(rec, raw):
    """Các cặp (cột curated, giá trị suy ra trực tiếp từ raw) phải bằng nhau."""
    if rec["source"] == "numinamath":
        return {"nl_problem": _nfc(raw["problem"]), "nl_solution": _nfc(raw["solution"]), "subset": raw["source"]}
    if rec["source"] == "proofnet":
        return {"source_record_key": raw["id"], "nl_problem": _nfc(raw["nl_statement"]),
                "formal_statement": _nfc(raw["formal_statement"])}
    return {"lean_full_name": _nfc(raw["full_name"]), "lean_file_path": raw["file_path"],
            "lean_start_line": raw["start"][0], "num_tactics": len(raw["traced_tactics"])}


def trace(lake_table, storage, manifest, record_ids):
    """lake_table: thư mục Parquet math_record; manifest: {raw_uri: entry}. Trả về danh sách kết quả từng record."""
    ids = ", ".join(f"'{i}'" for i in record_ids)
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")
    rows = con.execute(f"""SELECT record_id, source, source_version, source_record_key, raw_uri, raw_row, raw_sha256,
        license, nl_problem, nl_solution, subset, formal_statement, lean_full_name, lean_file_path,
        lean_start_line, num_tactics
        FROM read_parquet('{Path(lake_table).as_posix()}/**/*.parquet', hive_partitioning=true)
        WHERE record_id IN ({ids})""").fetchall()
    cols = [d[0] for d in con.description]
    out = []
    for row in rows:
        rec = dict(zip(cols, row))
        m = manifest.get(rec["raw_uri"], {})
        sha_ok = rec["raw_sha256"] == m.get("sha256") == _sha(str(Path(storage) / rec["raw_uri"]))
        raw = read_raw_row(storage, rec["raw_uri"], rec["raw_row"])
        exp = _expected(rec, raw)
        diff = [k for k, v in exp.items() if rec[k] != v]
        out.append({"record_id": rec["record_id"], "source": rec["source"], "raw_uri": rec["raw_uri"],
                    "raw_row": rec["raw_row"], "license": rec["license"], "raw_sha256_ok": sha_ok,
                    "fields_checked": list(exp), "fields_mismatch": diff, "ok": sha_ok and not diff})
    return out
