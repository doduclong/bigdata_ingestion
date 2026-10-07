"""Baseline bắt buộc: JSONL thô + Python tuần tự trên một máy, không partition, không tối ưu định dạng.

Đầu vào : thư mục staging (JSONL) của một mức quy mô.
Đầu ra  : <out>/math_record.jsonl (một tệp), <out>/errors.jsonl, <out>/read_errors.jsonl
"""
import collections
import json
import time
from pathlib import Path

from .readers import dumps
from .schema import FIELD_NAMES
from .scales import MAIN
from .staging import iter_jsonl, load_corpus_lookups, staging_files
from .transform import to_unified, validate


def run_baseline(staging_root, out_dir, manifest, run_id, timeout_s=None):
    staging_root, out_dir = Path(staging_root), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    code, imports = load_corpus_lookups(staging_root)
    t_lookup = time.perf_counter() - t0
    ctx = {"manifest": manifest, "premise_code": code, "file_imports": imports, "run_id": run_id}
    read_errors, seen = [], set()
    n_in = n_out = 0
    per_source = collections.Counter()
    err_codes, flags = collections.Counter(), collections.Counter()
    in_files = [p for s in MAIN for p in staging_files(staging_root, s)]
    status = "ok"
    with open(out_dir / "math_record.jsonl", "w", encoding="utf-8", newline="\n") as fo, \
            open(out_dir / "errors.jsonl", "w", encoding="utf-8", newline="\n") as fe:
        for s in iter_jsonl(in_files, read_errors):
            n_in += 1
            try:
                r = to_unified(s, ctx)
                errs = validate(r)
            except Exception as e:  # bản ghi làm hỏng hàm ánh xạ: ghi lỗi, không dừng pipeline
                r = {"record_id": None, "source": s.get("_source"), "raw_uri": s.get("_raw_uri"),
                     "raw_row": s.get("_raw_row")}
                errs = [f"E04_TRANSFORM:{type(e).__name__}"]
            key = (r.get("record_id"), r.get("source_version"))
            if not errs and key in seen:
                errs = ["E06_DUPLICATE_KEY"]
            if errs:
                err_codes.update(e.split(":")[0] for e in errs)
                fe.write(dumps({"record_id": r.get("record_id"), "source": r.get("source"),
                                "raw_uri": r.get("raw_uri"), "raw_row": r.get("raw_row"), "errors": errs}) + "\n")
                continue
            seen.add(key)
            flags.update(r["quality_flags"])
            per_source[r["source"]] += 1
            fo.write(dumps({k: r[k] for k in FIELD_NAMES}) + "\n")
            n_out += 1
            if timeout_s and time.perf_counter() - t0 > timeout_s:
                status = "timeout"
                break
    with open(out_dir / "read_errors.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for e in read_errors:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    seconds = time.perf_counter() - t0
    bytes_in = sum(p.stat().st_size for p in in_files) + sum(
        p.stat().st_size for s in ("leandojo_premise", "leandojo_file") for p in staging_files(staging_root, s))
    return {
        "status": status,
        "records_in": n_in,
        "records_out": n_out,
        "records_error": sum(1 for _ in open(out_dir / "errors.jsonl", encoding="utf-8")),
        "read_errors": len(read_errors),
        "schema_error_rate": round((n_in - n_out + len(read_errors)) / max(1, n_in + len(read_errors)), 6),
        "per_source": dict(per_source),
        "error_codes": dict(err_codes),
        "quality_flags": dict(flags),
        "lookup_load_s": round(t_lookup, 3),
        "elapsed_s": round(seconds, 3),
        "throughput_rps": round(n_in / seconds, 1),
        "bytes_in": bytes_in,
        "bytes_out": sum(p.stat().st_size for p in out_dir.glob("*.jsonl")),
        "files_out": len(list(out_dir.glob("*.jsonl"))),
    }
