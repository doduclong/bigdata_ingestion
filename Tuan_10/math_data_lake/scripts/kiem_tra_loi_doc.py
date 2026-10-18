"""Báo cáo lỗi đọc: tiêm 8 loại dòng hỏng vào bản sao mức 10K và kiểm tra baseline phát hiện đúng, không dừng.

Chạy: python scripts/kiem_tra_loi_doc.py
"""
import collections
import json
import shutil
from pathlib import Path

import _path  # noqa: F401
from mdl.baseline import run_baseline
from mdl.config import STORAGE
from mdl.manifest import load_manifest

src = STORAGE / "staging_scales" / "n=10k"
dst = STORAGE / "staging_faulty"
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree(src, dst)

numina = [p for p in sorted((dst / "numinamath").glob("*/*.jsonl")) if p.stat().st_size][0]
proof = [p for p in sorted((dst / "proofnet").glob("*/*.jsonl")) if p.stat().st_size][0]
good = json.loads(open(numina, encoding="utf-8").readline())
good_pn = json.loads(open(proof, encoding="utf-8").readline())


def line(obj):
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")


cases = [
    ("JSON bị cắt cụt", b'{"_source":"numinamath","_key":\n', "E05_PARSE"),
    ("Byte không phải UTF-8", b'{"_source":"numinamath","problem":"\xff\xfe"}\n', "E05_PARSE"),
    ("JSON không phải object", b"[1,2,3]\n", "E05_PARSE"),
    ("Thiếu nội dung (problem rỗng)", line({**good, "_key": "inject:1", "problem": ""}), "E03_EMPTY_CONTENT"),
    ("Nguồn không hợp lệ", line({**good, "_key": "inject:2", "_source": "unknown"}), "E04_TRANSFORM"),
    ("Trùng khóa (dòng lặp lại)", line(good), "E06_DUPLICATE_KEY"),
    ("raw_uri không có trong manifest", line({**good, "_key": "inject:3", "_raw_uri": "raw/x.parquet"}),
     "E01_MISSING_REQUIRED"),
]
with open(numina, "ab") as f:
    for _, b, _ in cases:
        f.write(b)
with open(proof, "ab") as f:
    f.write(line({**good_pn, "_key": "inject|4", "formal_statement": None}))
cases.append(("ProofNet thiếu formal_statement", b"", "E03_EMPTY_CONTENT"))

out = STORAGE / "out" / "faulty"
res = run_baseline(dst, out, load_manifest("manifest/manifest_full.json"), "fault-injection")
found = collections.Counter()
for l in open(out / "read_errors.jsonl", encoding="utf-8"):
    found[json.loads(l)["error"].split(":")[0]] += 1
for l in open(out / "errors.jsonl", encoding="utf-8"):
    for e in json.loads(l)["errors"]:
        found[e.split(":")[0]] += 1
expected = collections.Counter(c[2] for c in cases)
report = {
    "cases": [{"case": c[0], "expected_code": c[2]} for c in cases],
    "expected": dict(expected),
    "detected": dict(found),
    "all_detected": all(found[k] >= v for k, v in expected.items()),
    "records_out": res["records_out"],
    "records_out_expected": 10_000,
    "pipeline_completed": res["status"] == "ok",
    "read_errors_sample": [json.loads(l) for l in open(out / "read_errors.jsonl", encoding="utf-8")],
    "record_errors_sample": [json.loads(l) for l in open(out / "errors.jsonl", encoding="utf-8")],
}
Path("results/raw").mkdir(parents=True, exist_ok=True)
Path("results/raw/fault_injection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: report[k] for k in ("expected", "detected", "all_detected", "records_out")}, ensure_ascii=False))
