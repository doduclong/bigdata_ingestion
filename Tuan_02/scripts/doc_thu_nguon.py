"""Đọc thử cả 3 nguồn (raw đầy đủ hoặc raw sample), đếm bản ghi, lỗi đọc, thời gian.

Chạy: python scripts/doc_thu_nguon.py --raw data_sample/raw
      python scripts/doc_thu_nguon.py --raw ../_storage/raw --out ket_qua/doc_thu_full.json
"""
import argparse
import json
import time
from pathlib import Path

import psutil

import _path  # noqa: F401
from mdl.readers import novel_premises_index, read_leandojo_corpus, read_leandojo_theorems, read_numinamath, \
    read_proofnet

ap = argparse.ArgumentParser()
ap.add_argument("--raw", default="data_sample/raw")
ap.add_argument("--out", default=None)
a = ap.parse_args()
proc = psutil.Process()
report = {"raw": a.raw, "sources": {}}
jobs = {
    "numinamath": lambda: read_numinamath(a.raw),
    "proofnet": lambda: read_proofnet(a.raw),
    "leandojo": lambda: read_leandojo_theorems(a.raw, novel_premises_index(a.raw)),
    "leandojo_corpus": lambda: read_leandojo_corpus(a.raw),
}
for name, make in jobs.items():
    t0, n, errors, first = time.perf_counter(), 0, 0, None
    try:
        for rec in make():
            n += 1
            first = first or rec
    except Exception as e:  # lỗi đọc được ghi lại, không che giấu
        errors += 1
        report.setdefault("errors", []).append(f"{name}: {type(e).__name__}: {e}")
    report["sources"][name] = {"records": n, "read_errors": errors, "seconds": round(time.perf_counter() - t0, 2),
                               "rss_mb_after": round(proc.memory_info().rss / 2**20), "first_keys": sorted(
                                   (first[1] if isinstance(first, tuple) else first or {}).keys())}
    print(name, report["sources"][name]["records"], "records", report["sources"][name]["seconds"], "s")
if a.out:
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
