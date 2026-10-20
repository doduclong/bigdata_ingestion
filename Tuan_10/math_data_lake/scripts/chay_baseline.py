"""Chạy baseline end-to-end trên các mức quy mô, lặp N lần; ghi raw results theo Phụ lục B.

Chạy: python scripts/chay_baseline.py --scales 10k 100k full --repeat 3
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import _path  # noqa: F401
from mdl.config import STAGING, STORAGE
from mdl.manifest import load_manifest
from mdl.queries import run_queries
from mdl.sql_queries import jsonl_source, run_sql_queries
from mdl.runlog import Monitor, make_run, new_run_id, write_run
from mdl.baseline import run_baseline

ap = argparse.ArgumentParser()
ap.add_argument("--scales", nargs="+", default=["10k", "100k", "full"])
ap.add_argument("--repeat", type=int, default=3)
ap.add_argument("--timeout", type=int, default=3600)
ap.add_argument("--runs", default="results/raw/runs_baseline.jsonl")
ap.add_argument("--keep-output", action="store_true")
ap.add_argument("--sql", action="store_true", help="chạy thêm Q0-Q5 bằng DuckDB trên JSONL đầu ra")
a = ap.parse_args()

manifest = load_manifest("manifest/manifest_full.json")
ids = json.load(open("configs/query_ids.json"))["ids"] if Path("configs/query_ids.json").exists() else []
Path("logs").mkdir(exist_ok=True)
for scale in a.scales:
    src = STAGING if scale == "full" else STORAGE / "staging_scales" / f"n={scale}"
    for i in range(a.repeat):
        rid = new_run_id(f"baseline-{scale}")
        out = STORAGE / "out" / "baseline" / scale
        shutil.rmtree(out, ignore_errors=True)
        log = Path("logs") / f"{rid}.log"
        status = "ok"
        try:
            with Monitor() as m:
                res = run_baseline(src, out, manifest, rid, timeout_s=a.timeout)
            with Monitor() as mq:
                q = run_queries(out / "math_record.jsonl", ids)
            status = res["status"]
        except (Exception, KeyboardInterrupt) as e:  # gồm cả ngắt do chốt chặn RAM
            status, res, q = f"failed: {type(e).__name__}: {e}", {}, {}
            m = mq = None
        if a.sql and status == "ok":
            sq = run_sql_queries(jsonl_source((out / "math_record.jsonl").as_posix()), ids, threads=4)
            res = {**res, **{f"sql_{k}": v["seconds"] for k, v in sq.items()},
                   "sql_total_s": round(sum(v["seconds"] for v in sq.values()), 4)}
        metrics = {**(m.metrics() if m else {}), **res,
                   "query_total_s": round(sum(v["seconds"] for v in q.values()), 4),
                   "queries": {k: {"seconds": v["seconds"], "rows": v["rows"]} for k, v in q.items()}}
        log.write_text(json.dumps({"metrics": metrics, "query_results": {k: v["result"] for k, v in q.items()}},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        write_run(a.runs, make_run(rid, "baseline_jsonl_python", {"scale": scale, "repeat_idx": i,
                                                                  "input": str(src), "format": "jsonl",
                                                                  "partitioning": "none", "workers": 1},
                                   metrics, status, log, "manifest/manifest_full.json", timeout_s=a.timeout))
        print(f"{rid} {status} runtime={metrics.get('runtime_s')}s thr={metrics.get('throughput_rps')} "
              f"rss={metrics.get('peak_rss_mb')}MB q={metrics['query_total_s']}s", flush=True)
        if not a.keep_output and i < a.repeat - 1:
            shutil.rmtree(out, ignore_errors=True)
