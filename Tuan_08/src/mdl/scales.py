"""Tạo các mức quy mô (10K, 100K, 500K, ...) từ staging đầy đủ.

Quy tắc (cố định, tái lập):
- ProofNet (371 bản ghi) luôn lấy toàn bộ để mức nào cũng đủ 3 nguồn.
- Phần còn lại chia cho NuminaMath và LeanDojo theo tỷ lệ kích thước nguồn.
- Trong mỗi nguồn chọn các bản ghi có record_id nhỏ nhất (record_id là sha1 => giống chọn ngẫu nhiên đều).
- Bảng phụ corpus LeanDojo (bảng tra cứu kích thước cố định) được sao nguyên ở mọi mức.
"""
import json
import shutil
from pathlib import Path

from .staging import iter_jsonl, staging_files
from .transform import record_id

SCALES = {"10k": 10_000, "100k": 100_000, "500k": 500_000}
MAIN = ("numinamath", "proofnet", "leandojo")
LOOKUPS = ("leandojo_premise", "leandojo_file")


def quotas(n_total, sizes):
    rest = n_total - sizes["proofnet"]
    big = sizes["numinamath"] + sizes["leandojo"]
    q_lean = round(rest * sizes["leandojo"] / big)
    return {"proofnet": sizes["proofnet"], "leandojo": q_lean, "numinamath": rest - q_lean}


def build_scales(staging_root, out_root, scales=SCALES, log=print):
    staging_root, out_root = Path(staging_root), Path(out_root)
    ids, sizes = {}, {}
    for src in MAIN:
        ids[src] = sorted(record_id(r["_source"], r["_key"]) for r in iter_jsonl(staging_files(staging_root, src)))
        sizes[src] = len(ids[src])
    result = {}
    for name, n in scales.items():
        q = quotas(n, sizes)
        dest = out_root / f"n={name}"
        shutil.rmtree(dest, ignore_errors=True)
        for src in MAIN:
            keep = set(ids[src][:q[src]])
            for p in staging_files(staging_root, src):
                out = dest / p.relative_to(staging_root)
                out.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "rb") as f, open(out, "wb") as g:
                    for line in f:
                        r = json.loads(line)
                        if record_id(r["_source"], r["_key"]) in keep:
                            g.write(line)
        for lk in LOOKUPS:
            shutil.copytree(staging_root / lk, dest / lk)
        result[name] = q
        log(f"[scale] {name}: {q}")
    result["full"] = sizes
    return result
