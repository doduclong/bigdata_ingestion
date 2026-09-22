"""Tạo raw sample hợp pháp (cùng định dạng, cùng bố cục với raw đầy đủ) để đưa vào Git.

Chọn bản ghi xác định bằng hash (không dùng RNG) => chạy lại cho đúng cùng mẫu.
Mỗi bản ghi mẫu mang `_orig_row` = vị trí trong tệp gốc, nên khóa/record_id trùng với dữ liệu đầy đủ.
"""
import hashlib
import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .manifest import LEANDOJO_DIR


def _rank(key):
    return hashlib.sha1(f"sample|{key}".encode("utf-8")).hexdigest()


def _pick(keys, n):
    return sorted(sorted(range(len(keys)), key=lambda i: _rank(keys[i]))[:n])


def sample_numinamath(raw, out, per_subset=53, n_test=20):
    src, dst = Path(raw) / "numinamath", Path(out) / "numinamath"
    dst.mkdir(parents=True, exist_ok=True)
    for name, per in (("train-00000-of-00005.parquet", per_subset), ("test-00000-of-00001.parquet", None)):
        t = pq.read_table(src / name)
        t = t.append_column("_orig_row", pa.array(range(t.num_rows), pa.int64()))
        stem = name.removesuffix(".parquet")
        keys = [f"{stem}:{i}" for i in range(t.num_rows)]
        if per is None:
            idx = _pick(keys, n_test)
        else:
            idx = []
            subsets = t.column("source").to_pylist()
            for s in sorted(set(subsets)):
                rows = [i for i, v in enumerate(subsets) if v == s]
                idx += [rows[j] for j in _pick([keys[i] for i in rows], per)]
            idx.sort()
        pq.write_table(t.take(pa.array(idx)), dst / name)
    return sum(pq.read_metadata(p).num_rows for p in dst.glob("*.parquet"))


def sample_proofnet(raw, out, per_file=100):
    src, dst = Path(raw) / "proofnet", Path(out) / "proofnet"
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for name in ("valid.jsonl", "test.jsonl"):
        lines = open(src / name, encoding="utf-8").read().splitlines()
        recs = [json.loads(l) for l in lines]
        idx = _pick([r["id"] for r in recs], per_file)
        with open(dst / name, "w", encoding="utf-8", newline="\n") as f:
            for i in idx:
                f.write(json.dumps({**recs[i], "_orig_row": i}, ensure_ascii=False) + "\n")
        n += len(idx)
    shutil.copy(src / "LICENSE", dst / "LICENSE")
    return n


def sample_leandojo(raw, out, n=(("train", 250), ("val", 25), ("test", 25))):
    src, dst = Path(raw) / "leandojo" / LEANDOJO_DIR, Path(out) / "leandojo" / LEANDOJO_DIR
    (dst / "random").mkdir(parents=True, exist_ok=True)
    (dst / "novel_premises").mkdir(parents=True, exist_ok=True)
    chosen = set()
    total = 0
    for split, k in n:
        data = json.load(open(src / "random" / f"{split}.json", encoding="utf-8"))
        idx = _pick([f"{r['file_path']}::{r['full_name']}" for r in data], k)
        sel = [{**data[i], "_orig_row": i} for i in idx]
        chosen |= {(r["file_path"], r["full_name"]) for r in sel}
        json.dump(sel, open(dst / "random" / f"{split}.json", "w", encoding="utf-8"), ensure_ascii=False)
        total += len(sel)
    for split in ("train", "val", "test"):
        data = json.load(open(src / "novel_premises" / f"{split}.json", encoding="utf-8"))
        sel = [{**r, "_orig_row": i} for i, r in enumerate(data) if (r["file_path"], r["full_name"]) in chosen]
        json.dump(sel, open(dst / "novel_premises" / f"{split}.json", "w", encoding="utf-8"), ensure_ascii=False)
    files = {p for p, _ in chosen}
    with open(src / "corpus.jsonl", encoding="utf-8") as f, \
            open(dst / "corpus.jsonl", "w", encoding="utf-8", newline="\n") as g:
        for i, line in enumerate(f):
            r = json.loads(line)
            if r["path"] in files:
                r["premises"] = [p for p in r["premises"] if (r["path"], p["full_name"]) in chosen]
                r["_orig_row"] = i
                g.write(json.dumps(r, ensure_ascii=False) + "\n")
    shutil.copy(src / "metadata.json", dst / "metadata.json")
    (dst / "licenses").mkdir(exist_ok=True)
    shutil.copy(src / "licenses" / "README.md", dst / "licenses" / "README.md")
    return total


def make_raw_sample(raw, out):
    return {
        "numinamath": sample_numinamath(raw, out),
        "proofnet": sample_proofnet(raw, out),
        "leandojo": sample_leandojo(raw, out),
    }
