"""Bộ truy vấn kiểm tra chuẩn. Bản baseline: quét tuần tự tệp JSONL bằng Python (không chỉ mục).

Mỗi hàm trả kết quả đã chuẩn hóa (list/tuple sắp xếp) để so khớp với bản SQL ở các tuần sau.
"""
import collections
import json
import time


def _scan(path):
    with open(path, "rb") as f:
        for line in f:
            yield json.loads(line)


def q1_count_by_source_split(path, **_):
    c = collections.Counter((r["source"], r["split"]) for r in _scan(path))
    return sorted((s, sp, n) for (s, sp), n in c.items())


def q2_olympiad_latex(path, **_):
    n = total = 0
    for r in _scan(path):
        if r["source"] == "numinamath" and r["subset"] == "olympiads" and r["has_latex"]:
            n += 1
            total += len(r["nl_problem"])
    return [(n, round(total / n, 2) if n else None)]


def q3_point_lookup(path, ids=(), **_):
    want = set(ids)
    return sorted((r["record_id"], r["source"], r["content_sha256"]) for r in _scan(path) if r["record_id"] in want)


def q4_top_premises(path, k=10, **_):
    c = collections.Counter()
    for r in _scan(path):
        if r["source"] == "leandojo":
            c.update(r["premises"])
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))[:k]


def q5_provenance_audit(path, **_):
    prov = ("source", "source_version", "raw_uri", "raw_row", "raw_sha256", "license", "source_url",
            "downloaded_at", "ingest_run_id")
    c = collections.Counter()
    for r in _scan(path):
        complete = all(r.get(k) is not None for k in prov)
        c[(r["source"], r["license"], complete)] += 1
    return sorted((s, lic, ok, n) for (s, lic, ok), n in c.items())


QUERIES = {
    "Q1_count_by_source_split": q1_count_by_source_split,
    "Q2_olympiad_latex": q2_olympiad_latex,
    "Q3_point_lookup": q3_point_lookup,
    "Q4_top_premises": q4_top_premises,
    "Q5_provenance_audit": q5_provenance_audit,
}


def run_queries(path, ids):
    out = {}
    for name, fn in QUERIES.items():
        t0 = time.perf_counter()
        res = fn(path, ids=ids)
        out[name] = {"seconds": round(time.perf_counter() - t0, 4), "rows": len(res), "result": res}
    return out
