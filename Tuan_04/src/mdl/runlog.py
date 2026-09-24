"""Ghi nhận một lần chạy theo mẫu Phụ lục B + đo peak RAM / bytes I/O bằng luồng lấy mẫu psutil."""
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import _thread
import threading
import time
import uuid
from importlib import metadata
from pathlib import Path

import psutil

SRC = Path(__file__).resolve().parents[1]


def code_version():
    """Commit git nếu có; nếu không, sha256 rút gọn của toàn bộ mã nguồn src/."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=SRC, capture_output=True, text=True,
                             timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return "git-" + out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    h = hashlib.sha256()
    for p in sorted(SRC.rglob("*.py")):
        h.update(p.read_bytes())
    return "src-" + h.hexdigest()[:12]


def data_version(manifest_path):
    return "manifest-" + hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()[:12]


def machine():
    vm = psutil.virtual_memory()
    return {"os": platform.platform(), "cpu": platform.processor(), "cores_physical": psutil.cpu_count(False),
            "cores_logical": psutil.cpu_count(), "ram_gb": round(vm.total / 2**30, 1)}


def software():
    sw = {"python": sys.version.split()[0]}
    for pkg in ("pyarrow", "duckdb", "pyspark", "pandas", "psutil"):
        try:
            sw[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    try:
        out = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
        sw["java"] = (out.stderr or out.stdout).splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        pass
    return sw


def new_run_id(tag):
    return f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{tag}-{uuid.uuid4().hex[:6]}"


# Giới hạn an toàn cho máy dùng chung: tổng RSS (Python + JVM) <= 3,5 GB và luôn chừa >= 3 GB RAM trống
MAX_RSS_MB = 3500
MIN_FREE_MB = 3000


class MemoryGuardError(RuntimeError):
    pass


def check_free_memory(min_free_mb=MIN_FREE_MB):
    free = psutil.virtual_memory().available / 2**20
    if free < min_free_mb:
        raise MemoryGuardError(f"RAM trống {free:.0f} MB < {min_free_mb} MB — không chạy để tránh treo máy")


class Monitor:
    """Lấy mẫu RSS (tiến trình + các tiến trình con, ví dụ JVM của Spark) và I/O mỗi `interval` giây.

    Nếu RSS vượt `max_rss_mb` hoặc RAM trống của máy xuống dưới `min_free_mb`, ngắt luồng chính (KeyboardInterrupt).
    """

    def __init__(self, interval=0.1, max_rss_mb=MAX_RSS_MB, min_free_mb=MIN_FREE_MB):
        self.interval, self.peak_rss, self._stop = interval, 0, threading.Event()
        self.max_rss_mb, self.min_free_mb, self.tripped = max_rss_mb, min_free_mb, None
        self.proc = psutil.Process()

    def _procs(self):
        try:
            return [self.proc] + self.proc.children(recursive=True)
        except (psutil.Error, OSError):
            return [self.proc]

    def _io(self):
        r = w = 0
        for p in self._procs():
            try:
                c = p.io_counters()
                r, w = r + c.read_bytes, w + c.write_bytes
            except psutil.Error:
                pass
        return r, w

    def _loop(self):
        while not self._stop.is_set():
            rss = 0
            for p in self._procs():
                try:
                    rss += p.memory_info().rss
                except psutil.Error:
                    pass
            self.peak_rss = max(self.peak_rss, rss)
            free = psutil.virtual_memory().available / 2**20
            if self.tripped is None and (rss / 2**20 > self.max_rss_mb or free < self.min_free_mb):
                self.tripped = f"memory guard: rss={rss / 2**20:.0f}MB free={free:.0f}MB"
                for p in self._procs()[1:]:  # dừng JVM con trước
                    try:
                        p.kill()
                    except psutil.Error:
                        pass
                _thread.interrupt_main()
            r, w = self._io()
            self._last_io = (max(r, self._last_io[0]), max(w, self._last_io[1]))
            self._stop.wait(self.interval)

    def __enter__(self):
        check_free_memory(self.min_free_mb)
        self.io0 = self._io()
        self._last_io = self.io0
        self.t0 = time.perf_counter()
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self.t0
        r, w = self._io()
        self._stop.set()
        self._th.join()
        # tiến trình con (JVM) có thể đã thoát => dùng giá trị lớn nhất quan sát được
        r, w = max(r, self._last_io[0]), max(w, self._last_io[1])
        self.read_bytes, self.write_bytes = r - self.io0[0], w - self.io0[1]
        return False

    def metrics(self):
        return {"runtime_s": round(self.seconds, 3), "peak_rss_mb": round(self.peak_rss / 2**20, 1),
                "read_bytes": self.read_bytes, "write_bytes": self.write_bytes}


def write_run(path, run):
    """Nối một bản ghi lần chạy (JSON Lines) — raw results không chỉnh tay."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(run, ensure_ascii=False) + "\n")


def make_run(run_id, experiment, params, metrics, status, log_path, manifest_path, seed=0, timeout_s=None):
    return {
        "run_id": run_id,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "experiment": experiment,
        "git_commit": code_version(),
        "data_version": data_version(manifest_path),
        "machine": machine(),
        "software": software(),
        "parameters": params,
        "seed": seed,
        "timeout_s": timeout_s,
        "metrics": metrics,
        "status": status,
        "log": str(log_path),
    }
