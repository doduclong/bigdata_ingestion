"""Load test nhỏ cho API dữ liệu trên kho đầy đủ: 1, 10, 50 client đồng thời, lặp 3 lần.

Hỗn hợp truy vấn (cố định, seed 42): 70% GET /records/{id}, 20% GET /records?source&subset&limit=50,
10% GET /premises/{p}/theorems. Đo P50/P95/P99, QPS, lỗi, peak RSS của tiến trình server.
Chạy: python scripts/load_test_api.py [--requests 1500]
"""
import argparse
import random
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb
import httpx
import psutil

import _path  # noqa: F401
from mdl.config import STORAGE
from mdl.runlog import make_run, new_run_id, write_run

ap = argparse.ArgumentParser()
ap.add_argument("--requests", type=int, default=1500)
ap.add_argument("--repeat", type=int, default=3)
ap.add_argument("--port", type=int, default=8765)
ap.add_argument("--runs", default="results/raw/tuan_10/runs_api_load.jsonl")
a = ap.parse_args()
LAKE = STORAGE / "lake" / "math_record"
URL = f"http://127.0.0.1:{a.port}"

con = duckdb.connect()
con.execute("SET memory_limit='1GB'")
src = f"read_parquet('{LAKE.as_posix()}/**/*.parquet', hive_partitioning=true)"
ids = [r[0] for r in con.execute(f"SELECT record_id FROM {src} USING SAMPLE 5000 ROWS (reservoir, 42)").fetchall()]
subsets = con.execute(f"SELECT DISTINCT source, subset FROM {src} WHERE source <> 'leandojo' ORDER BY ALL").fetchall()
prems = [r[0] for r in con.execute(f"SELECT p FROM (SELECT unnest(premises) p FROM {src} WHERE source='leandojo') "
                                   "GROUP BY p ORDER BY count(*) DESC LIMIT 200").fetchall()]
con.close()
rng = random.Random(42)


def make_requests(n):
    out = []
    for _ in range(n):
        x = rng.random()
        if x < 0.7:
            out.append(f"/records/{rng.choice(ids)}")
        elif x < 0.9:
            s, sub = rng.choice(subsets)
            out.append(f"/records?source={s}&subset={sub}&limit=50")
        else:
            out.append(f"/premises/{rng.choice(prems)}/theorems?limit=20")
    return out


server = subprocess.Popen([sys.executable, "scripts/mdl.py", "serve", "--port", str(a.port)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
proc = psutil.Process(server.pid)
for _ in range(120):
    try:
        if httpx.get(URL + "/health", timeout=30).status_code == 200:
            break
    except httpx.HTTPError:
        time.sleep(1)
peak = {"rss": 0}
stop = threading.Event()


def watch():
    while not stop.is_set():
        try:
            rss = sum(p.memory_info().rss for p in [proc] + proc.children(recursive=True))
            peak["rss"] = max(peak["rss"], rss)
        except psutil.Error:
            pass
        stop.wait(0.1)


threading.Thread(target=watch, daemon=True).start()
Path(a.runs).parent.mkdir(parents=True, exist_ok=True)
try:
    httpx.get(URL + "/records?limit=10", timeout=60)  # khởi động: nạp metadata Parquet
    for rep in range(a.repeat):
        for conc in (1, 10, 50):
            reqs = make_requests(a.requests)
            lat, errors = [], 0
            client = httpx.Client(base_url=URL, timeout=60, limits=httpx.Limits(max_connections=conc))

            def call(path):
                t0 = time.perf_counter()
                r = client.get(path)
                return time.perf_counter() - t0, r.status_code

            t0 = time.perf_counter()
            with ThreadPoolExecutor(conc) as ex:
                for dt, code in ex.map(call, reqs):
                    lat.append(dt * 1000)
                    errors += code != 200
            wall = time.perf_counter() - t0
            client.close()
            lat.sort()
            m = {"requests": len(reqs), "errors": errors, "wall_s": round(wall, 3), "qps": round(len(reqs) / wall, 1),
                 "p50_ms": round(statistics.median(lat), 2), "p95_ms": round(lat[int(0.95 * len(lat)) - 1], 2),
                 "p99_ms": round(lat[int(0.99 * len(lat)) - 1], 2), "server_peak_rss_mb": round(peak["rss"] / 2**20)}
            write_run(a.runs, make_run(new_run_id(f"api-c{conc}"), "api_load", {"concurrency": conc,
                                                                               "repeat_idx": rep, "mix": "70/20/10",
                                                                               "seed": 42}, m, "ok", "-",
                                       "manifest/manifest_full.json", seed=42))
            print(rep, conc, m, flush=True)
finally:
    stop.set()
    server.terminate()
    server.wait(10)
