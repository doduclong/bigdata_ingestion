"""Tạo data_sample/: raw sample (~1.000 bản ghi) + manifest/checksum + staging + curated sample theo lược đồ chung.

Chạy: python scripts/tao_mau.py
Kết quả: data_sample/raw/..., data_sample/manifest_sample.json, data_sample/checksums.sha256,
         data_sample/curated/math_record_sample.{jsonl,parquet}, data_sample/curated/errors_sample.jsonl
"""
import collections
import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import _path  # noqa: F401
from mdl.config import RAW
from mdl.manifest import build_manifest, load_manifest
from mdl.readers import dumps
from mdl.sample import make_raw_sample
from mdl.schema import FIELD_NAMES, arrow_schema
from mdl.staging import build_staging, iter_jsonl, load_corpus_lookups, staging_files
from mdl.transform import to_unified, validate

OUT = Path("data_sample")
raw_s, stg_s, cur_s = OUT / "raw", OUT / "staging", OUT / "curated"
for d in (raw_s, stg_s, cur_s):
    shutil.rmtree(d, ignore_errors=True)

counts = make_raw_sample(RAW, raw_s)
print("raw sample:", counts)
m = build_manifest(raw_s)
# Bản ghi mẫu giữ số dòng gốc => provenance phải trỏ về tệp raw ĐẦY ĐỦ (sha256, ngày tải);
# hash của chính tệp mẫu lưu ở sample_sha256 để kiểm tra toàn vẹn bản mẫu.
full = load_manifest("manifest/manifest_full.json")
for e in m["files"]:
    f = full[e["raw_uri"]]
    e.update(sample_sha256=e["sha256"], sample_bytes=e["bytes"], sha256=f["sha256"], bytes=f["bytes"],
             downloaded_at=f["downloaded_at"])
(OUT / "manifest_sample.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
with open(OUT / "checksums.sha256", "w", encoding="utf-8", newline="\n") as f:
    for e in m["files"]:
        f.write(f"{e['sample_sha256']}  {e['raw_uri']}\n")

build_staging(raw_s, stg_s)
code, imports = load_corpus_lookups(stg_s)
ctx = {"manifest": load_manifest(OUT / "manifest_sample.json"), "premise_code": code, "file_imports": imports,
       "run_id": "sample-w02"}
cur_s.mkdir(parents=True)
good, bad, flags = [], [], collections.Counter()
for src in ("numinamath", "proofnet", "leandojo"):
    for s in iter_jsonl(staging_files(stg_s, src)):
        r = to_unified(s, ctx)
        errs = validate(r)
        if errs:
            bad.append({"record_id": r["record_id"], "source": src, "raw_uri": r["raw_uri"], "raw_row": r["raw_row"],
                        "errors": errs})
        else:
            good.append(r)
            flags.update(r["quality_flags"])
with open(cur_s / "math_record_sample.jsonl", "w", encoding="utf-8", newline="\n") as f:
    for r in good:
        f.write(dumps({k: r[k] for k in FIELD_NAMES}) + "\n")
with open(cur_s / "errors_sample.jsonl", "w", encoding="utf-8", newline="\n") as f:
    for r in bad:
        f.write(dumps(r) + "\n")
pq.write_table(pa.Table.from_pylist(good, schema=arrow_schema()), cur_s / "math_record_sample.parquet")
by_src = collections.Counter(r["source"] for r in good)
summary = {"raw_sample": counts, "curated": dict(by_src), "errors": len(bad), "quality_flags": dict(flags)}
(OUT / "sample_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary))
