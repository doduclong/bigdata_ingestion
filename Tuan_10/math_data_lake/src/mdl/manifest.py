"""Tải snapshot có phiên bản cố định vào vùng raw và lập manifest (sha256, kích thước, ngày tải, giấy phép)."""
import datetime as dt
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

from .config import RAW, SOURCES

LEANDOJO_DIR = "leandojo_benchmark_4"
LEANDOJO_FILES = [
    "metadata.json", "corpus.jsonl", "licenses/README.md",
    "random/train.json", "random/val.json", "random/test.json",
    "novel_premises/train.json", "novel_premises/val.json", "novel_premises/test.json",
]


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat(timespec="seconds")


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
        while block := r.read(1 << 20):
            f.write(block)
    tmp.replace(dest)


def fetch_all(root=RAW, sources=None, log=print):
    """Tải các tệp còn thiếu (đã có thì bỏ qua) và giải nén LeanDojo."""
    root = Path(root)
    for name, spec in SOURCES.items():
        if sources and name not in sources:
            continue
        for f in spec["files"]:
            dest = root / name / Path(f).name
            if dest.exists() and dest.stat().st_size > 0:
                log(f"[skip] {name}/{dest.name}")
                continue
            url = spec["base"] + f + ("/content" if name == "leandojo" else "")
            log(f"[get ] {url}")
            download(url, dest)
        if name == "leandojo" and not (root / name / LEANDOJO_DIR / "corpus.jsonl").exists():
            with tarfile.open(root / name / "leandojo_benchmark_4.tar.gz") as t:
                t.extractall(root / name, filter="data")


def build_manifest(root=RAW, out=None):
    """Liệt kê mọi tệp raw được pipeline dùng, kèm checksum. Ghi ra JSON nếu có `out`."""
    root = Path(root)
    entries = []

    def add(source, rel, kind, downloaded_at=None):
        p = root / source / rel
        if not p.exists():  # bản mẫu chỉ có một phần tệp
            return
        spec = SOURCES[source]
        st = p.stat()
        entries.append({
            "source": source,
            "source_version": spec["version"],
            "license": spec["license"],
            "source_url": spec["url"],
            "raw_uri": f"raw/{source}/{Path(rel).as_posix()}",
            "kind": kind,
            "bytes": st.st_size,
            "sha256": sha256_file(p),
            "downloaded_at": downloaded_at or _iso(st.st_mtime),
        })

    for f in SOURCES["numinamath"]["files"]:
        add("numinamath", Path(f).name, "download")
    for f in SOURCES["proofnet"]["files"]:
        add("proofnet", Path(f).name, "download")
    tar = root / "leandojo" / "leandojo_benchmark_4.tar.gz"
    tar_time = _iso(tar.stat().st_mtime) if tar.exists() else None
    if tar.exists():
        add("leandojo", tar.name, "download")
    for f in LEANDOJO_FILES:
        if (root / "leandojo" / LEANDOJO_DIR / f).exists():
            add("leandojo", f"{LEANDOJO_DIR}/{f}", "extracted", tar_time)

    # Dữ liệu do API nhận cũng thuộc raw; giữ provenance khi download lập lại manifest.
    for p in sorted((root / "api").rglob("*.jsonl")):
        record = json.loads(p.read_text(encoding="utf-8"))
        metadata = record["_submission"]
        entries.append({"source": metadata["source"], "source_version": metadata["source_version"],
                        "license": metadata["license"], "source_url": metadata["source_url"],
                        "raw_uri": "raw/" + p.relative_to(root).as_posix(), "kind": "api",
                        "bytes": p.stat().st_size, "sha256": sha256_file(p),
                        "downloaded_at": _iso(p.stat().st_mtime)})
    manifest = {
        "manifest_version": "1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sources": {k: {kk: v[kk] for kk in ("version", "license", "url")} for k, v in SOURCES.items()},
        "files": entries,
    }
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def load_manifest(path):
    m = json.loads(Path(path).read_text(encoding="utf-8"))
    return {e["raw_uri"]: e for e in m["files"]}


def verify(root, manifest_path):
    """Trả về danh sách tệp sai checksum hoặc bị thiếu."""
    bad = []
    for uri, e in load_manifest(manifest_path).items():
        p = Path(root).parent / uri
        if not p.exists():
            bad.append((uri, "missing"))
        elif sha256_file(p) != e["sha256"]:
            bad.append((uri, "sha256 mismatch"))
    return bad
