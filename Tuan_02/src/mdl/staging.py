"""Raw -> staging: ghi JSONL (một bản ghi/dòng) cho từng nguồn + 2 bảng phụ của corpus LeanDojo.

Bố cục:  <staging>/<source>/<source_version>/part-<raw-file>.jsonl
         <staging>/leandojo_premise/<v>/part-corpus.jsonl ; <staging>/leandojo_file/<v>/part-corpus.jsonl
"""
import json
import time
from pathlib import Path

from .config import RAW, SOURCES, STAGING
from .readers import dumps, novel_premises_index, read_leandojo_corpus, read_leandojo_theorems, read_numinamath, \
    read_proofnet


class _Writers:
    """Mở một tệp JSONL cho mỗi tệp raw nguồn (giữ tương ứng 1-1 raw -> staging)."""

    def __init__(self, base):
        self.base, self.files, self.rows, self.bytes = Path(base), {}, 0, 0

    def write(self, rec):
        name = "part-" + Path(rec["_raw_uri"]).name.split(".")[0] + ".jsonl"
        f = self.files.get(name)
        if f is None:
            self.base.mkdir(parents=True, exist_ok=True)
            f = self.files[name] = open(self.base / name, "w", encoding="utf-8", newline="\n")
        line = dumps(rec) + "\n"
        f.write(line)
        self.rows += 1
        self.bytes += len(line.encode("utf-8"))

    def close(self):
        for f in self.files.values():
            f.close()


def build_staging(raw_root=RAW, out_root=STAGING, sources=("numinamath", "proofnet", "leandojo"), log=print):
    raw_root, out_root = Path(raw_root), Path(out_root)
    stats = {}
    for src in sources:
        t0 = time.perf_counter()
        w = _Writers(out_root / src / SOURCES[src]["version"])
        if src == "numinamath":
            it = read_numinamath(raw_root)
        elif src == "proofnet":
            it = read_proofnet(raw_root)
        else:
            it = read_leandojo_theorems(raw_root, novel_premises_index(raw_root))
        for rec in it:
            w.write(rec)
        w.close()
        stats[src] = {"rows": w.rows, "bytes": w.bytes, "seconds": round(time.perf_counter() - t0, 2)}
        log(f"[staging] {src}: {w.rows} rows, {w.bytes / 1e6:.1f} MB, {stats[src]['seconds']} s")
        if src == "leandojo":
            t0 = time.perf_counter()
            v = SOURCES[src]["version"]
            wp, wf = _Writers(out_root / "leandojo_premise" / v), _Writers(out_root / "leandojo_file" / v)
            for kind, rec in read_leandojo_corpus(raw_root):
                (wp if kind == "premise" else wf).write(rec)
            wp.close()
            wf.close()
            stats["leandojo_corpus"] = {"premises": wp.rows, "files": wf.rows, "bytes": wp.bytes + wf.bytes,
                                        "seconds": round(time.perf_counter() - t0, 2)}
            log(f"[staging] leandojo corpus: {wp.rows} premises, {wf.rows} files")
    return stats


def iter_jsonl(paths, errors=None):
    """Đọc JSONL tuần tự; dòng hỏng được ghi vào `errors` (list) thay vì làm dừng pipeline."""
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for i, line in enumerate(f):
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    if errors is not None:
                        errors.append({"file": str(p), "line": i, "error": f"E05_PARSE:{e.msg}"})


def staging_files(root, source):
    return sorted((Path(root) / source).glob("*/*.jsonl"))


def load_corpus_lookups(root):
    """Nạp bảng phụ corpus thành dict để join (baseline Python)."""
    code, imports = {}, {}
    for r in iter_jsonl(staging_files(root, "leandojo_premise")):
        code.setdefault((r["path"], r["full_name"]), r["code"])  # trùng khóa: giữ bản đầu
    for r in iter_jsonl(staging_files(root, "leandojo_file")):
        imports[r["path"]] = r["imports"]
    return code, imports
