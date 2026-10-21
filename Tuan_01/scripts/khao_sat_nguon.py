"""Khảo sát 3 nguồn dữ liệu (Tuần 1): số bản ghi, trường, tỷ lệ rỗng, độ dài, phân bố nhóm con.

Chạy: python scripts/khao_sat_nguon.py --raw ../_storage/raw --out ket_qua/khao_sat_nguon.json
"""
import argparse
import collections
import json
import os
import re
import time
from pathlib import Path

import pyarrow.parquet as pq

LATEX = re.compile(r"\$[^$]+\$|\\\(|\\\[|\\begin\{")


def field_stats(values):
    n = len(values)
    empty = sum(1 for v in values if v is None or (isinstance(v, (str, list)) and len(v) == 0))
    lens = [len(v) for v in values if isinstance(v, (str, list)) and v]
    return {
        "n": n,
        "empty_rate": round(empty / n, 4) if n else None,
        "avg_len": round(sum(lens) / len(lens), 1) if lens else 0,
        "max_len": max(lens) if lens else 0,
    }


def survey_numina(root):
    files = sorted((root / "numinamath").glob("*.parquet"))
    out = {"files": [], "fields": {}, "subset": collections.Counter(), "rows": 0}
    cols = collections.defaultdict(list)
    latex = 0
    for f in files:
        meta = pq.ParquetFile(f).metadata
        out["files"].append({"file": f.name, "rows": meta.num_rows, "bytes": f.stat().st_size})
        out["rows"] += meta.num_rows
        t = pq.read_table(f, columns=["source", "problem", "solution"])
        out["subset"].update(t.column("source").to_pylist())
        # Thống kê trường lấy trên shard đầu (171K bản ghi) để tiết kiệm RAM
        if not cols and f.name.startswith("train"):
            for c in ["source", "problem", "solution"]:
                cols[c] = t.column(c).to_pylist()
            latex = sum(1 for p in cols["problem"] if p and LATEX.search(p))
    out["fields"] = {c: field_stats(v) for c, v in cols.items()}
    out["fields"]["messages"] = {"note": "list<struct<role,content>>; trùng nội dung problem/solution"}
    out["latex_rate_problem_shard0"] = round(latex / len(cols["problem"]), 4)
    out["subset"] = dict(out["subset"].most_common())
    return out


def survey_proofnet(root):
    out = {"files": [], "rows": 0, "subset": collections.Counter()}
    recs = []
    for name in ["valid.jsonl", "test.jsonl"]:
        f = root / "proofnet" / name
        rows = [json.loads(l) for l in f.open(encoding="utf-8")]
        out["files"].append({"file": name, "rows": len(rows), "bytes": f.stat().st_size})
        recs += rows
    out["rows"] = len(recs)
    out["subset"] = dict(collections.Counter(r["id"].split("|")[0] for r in recs).most_common())
    keys = sorted({k for r in recs for k in r})
    out["fields"] = {k: field_stats([r.get(k) for r in recs]) for k in keys}
    out["latex_rate_nl_statement"] = round(sum(1 for r in recs if LATEX.search(r["nl_statement"])) / len(recs), 4)
    return out


def survey_leandojo(root):
    base = root / "leandojo" / "leandojo_benchmark_4"
    meta = json.loads((base / "metadata.json").read_text(encoding="utf-8"))
    out = {"metadata": meta, "files": [], "rows": 0, "subset": collections.Counter()}
    recs = []
    for split in ["train", "val", "test"]:
        f = base / "random" / f"{split}.json"
        rows = json.load(f.open(encoding="utf-8"))
        out["files"].append({"file": f"random/{split}.json", "rows": len(rows), "bytes": f.stat().st_size})
        recs += rows
    out["rows"] = len(recs)
    out["subset"] = dict(collections.Counter(".".join(r["file_path"].split("/")[:2]) for r in recs).most_common(15))
    keys = sorted({k for r in recs for k in r})
    out["fields"] = {k: field_stats([r.get(k) for r in recs]) for k in keys}
    ntac = [len(r["traced_tactics"]) for r in recs]
    out["empty_traced_tactics_rate"] = round(sum(1 for x in ntac if x == 0) / len(ntac), 4)
    out["avg_tactics_nonempty"] = round(sum(ntac) / max(1, sum(1 for x in ntac if x)), 2)
    corpus = base / "corpus.jsonl"
    n_prem, n_files = 0, 0
    for line in corpus.open(encoding="utf-8"):
        n_files += 1
        n_prem += len(json.loads(line)["premises"])
    out["corpus"] = {"files": n_files, "premises": n_prem, "bytes": corpus.stat().st_size}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="../_storage/raw")
    ap.add_argument("--out", default="ket_qua/khao_sat_nguon.json")
    a = ap.parse_args()
    root = Path(a.raw)
    t0 = time.time()
    res = {
        "numinamath": survey_numina(root),
        "proofnet": survey_proofnet(root),
        "leandojo": survey_leandojo(root),
    }
    res["total_rows"] = sum(res[s]["rows"] for s in ["numinamath", "proofnet", "leandojo"])
    res["elapsed_s"] = round(time.time() - t0, 1)
    os.makedirs(Path(a.out).parent, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({s: res[s]["rows"] for s in ["numinamath", "proofnet", "leandojo"]}), "total", res["total_rows"])


if __name__ == "__main__":
    main()
