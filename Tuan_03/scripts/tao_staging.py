"""Raw -> staging JSONL cho toàn bộ snapshot, đo thời gian/RAM/I/O. Chạy: python scripts/tao_staging.py [--repeat 1]"""
import argparse

import _path  # noqa: F401
from mdl.config import RAW, STAGING
from mdl.runlog import Monitor, make_run, new_run_id, write_run
from mdl.staging import build_staging

ap = argparse.ArgumentParser()
ap.add_argument("--repeat", type=int, default=1)
ap.add_argument("--runs", default="results/raw/runs_ingest.jsonl")
a = ap.parse_args()
for i in range(a.repeat):
    rid = new_run_id("ingest")
    with Monitor() as m:
        stats = build_staging(RAW, STAGING)
    run = make_run(rid, "ingest_raw_to_staging", {"repeat_idx": i, "raw": str(RAW), "out": str(STAGING)},
                   {**m.metrics(), "stats": stats, "records": sum(v.get("rows", 0) for v in stats.values())},
                   "ok", "-", "manifest/manifest_full.json")
    write_run(a.runs, run)
    print(rid, m.metrics())
