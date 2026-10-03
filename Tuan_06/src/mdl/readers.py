"""Reader cho 3 nguồn: đọc tệp raw, sinh bản ghi staging (UTF-8 NFC, tên trường thống nhất, con trỏ raw).

Mỗi bản ghi staging có các trường meta tiền tố `_`:
  _source, _source_version, _key, _split, _raw_uri, _raw_row, _extra
và phần nội dung giữ tên trường gốc (snake_case).
"""
import json
import unicodedata
from pathlib import Path

import pyarrow.parquet as pq

from .config import RAW, SOURCES
from .manifest import LEANDOJO_DIR


def nfc(x):
    """Chuẩn hóa Unicode NFC đệ quy cho str/list/dict."""
    if isinstance(x, str):
        return unicodedata.normalize("NFC", x)
    if isinstance(x, list):
        return [nfc(v) for v in x]
    if isinstance(x, dict):
        return {k: nfc(v) for k, v in x.items()}
    return x


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _meta(source, key, split, raw_uri, raw_row, extra=None):
    return {
        "_source": source,
        "_source_version": SOURCES[source]["version"],
        "_key": key,
        "_split": split,
        "_raw_uri": raw_uri,
        "_raw_row": raw_row,
        "_extra": dumps(extra) if extra else None,
    }


def read_numinamath(root=RAW, files=None, batch_size=4096):
    d = Path(root) / "numinamath"
    for name in files or SOURCES["numinamath"]["files"]:
        p = d / name
        if not p.exists():
            continue
        stem = name.removesuffix(".parquet")
        split = stem.split("-")[0]
        pos = 0
        for batch in pq.ParquetFile(p).iter_batches(batch_size=batch_size):
            for r in batch.to_pylist():
                r = nfc(r)
                row = r.pop("_orig_row", pos)  # tệp mẫu giữ số dòng gốc trong cột _orig_row
                pos += 1
                msgs = r.get("messages") or []
                expected = [{"role": "user", "content": r["problem"]}, {"role": "assistant", "content": r["solution"]}]
                extra = {"messages": msgs} if msgs != expected else None
                rec = _meta("numinamath", f"{stem}:{row}", split, f"raw/numinamath/{name}", row, extra)
                rec.update(source=r.get("source"), problem=r.get("problem"), solution=r.get("solution"))
                yield rec


def read_proofnet(root=RAW):
    d = Path(root) / "proofnet"
    for name in ["valid.jsonl", "test.jsonl"]:
        p = d / name
        if not p.exists():
            continue
        split = name.removesuffix(".jsonl")
        with open(p, encoding="utf-8") as f:
            for row, line in enumerate(f):
                r = nfc(json.loads(line))
                row = r.pop("_orig_row", row)
                rec = _meta("proofnet", r["id"], split, f"raw/proofnet/{name}", row)
                for k in ("id", "nl_statement", "nl_proof", "formal_statement", "src_header"):
                    rec[k] = r.get(k)
                yield rec


def _theorem_key(r):
    return f"{r['file_path']}::{r['full_name']}"


def _tactics(traced):
    out = []
    for t in traced or []:
        ann = t.get("annotated_tactic") or ["", []]
        out.append({
            "tactic": t.get("tactic"),
            "annotated_tactic": ann[0] if ann else None,
            "premises": [p["full_name"] for p in (ann[1] if len(ann) > 1 else [])],
            "state_before": t.get("state_before"),
            "state_after": t.get("state_after"),
        })
    return out


def novel_premises_index(root=RAW):
    """Ánh xạ khóa định lý -> split trong cách chia `novel_premises` (để lưu vào _extra)."""
    base = Path(root) / "leandojo" / LEANDOJO_DIR / "novel_premises"
    idx = {}
    for split in ("train", "val", "test"):
        p = base / f"{split}.json"
        if p.exists():
            for r in json.load(open(p, encoding="utf-8")):
                idx[_theorem_key(r)] = split
    return idx


def read_leandojo_theorems(root=RAW, novel_index=None, splits=("train", "val", "test")):
    base = Path(root) / "leandojo" / LEANDOJO_DIR / "random"
    novel_index = novel_index or {}
    for split in splits:
        p = base / f"{split}.json"
        if not p.exists():
            continue
        data = json.load(open(p, encoding="utf-8"))  # mảng JSON: buộc phải nạp cả tệp
        for row, r in enumerate(data):
            r = nfc(r)
            row = r.pop("_orig_row", row)
            key = _theorem_key(r)
            extra = {"url": r.get("url"), "commit": r.get("commit"), "start": r.get("start"),
                     "end": r.get("end"), "split_novel_premises": novel_index.get(key)}
            rec = _meta("leandojo", key, split, f"raw/leandojo/{LEANDOJO_DIR}/random/{split}.json", row, extra)
            rec.update(file_path=r["file_path"], full_name=r["full_name"],
                       start_line=r["start"][0], end_line=r["end"][0], tactics=_tactics(r.get("traced_tactics")))
            yield rec
        del data


def read_leandojo_corpus(root=RAW):
    """Sinh 2 loại bản ghi: ('file', {...imports}) và ('premise', {...code})."""
    p = Path(root) / "leandojo" / LEANDOJO_DIR / "corpus.jsonl"
    uri = f"raw/leandojo/{LEANDOJO_DIR}/corpus.jsonl"
    with open(p, encoding="utf-8") as f:
        for row, line in enumerate(f):
            r = nfc(json.loads(line))
            row = r.pop("_orig_row", row)
            yield "file", {"path": r["path"], "imports": r.get("imports") or [], "_raw_uri": uri, "_raw_row": row}
            for i, prem in enumerate(r.get("premises") or []):
                yield "premise", {
                    "path": r["path"], "full_name": prem["full_name"], "code": prem.get("code"),
                    "kind": prem.get("kind"), "start_line": prem["start"][0], "end_line": prem["end"][0],
                    "_raw_uri": uri, "_raw_row": row, "_premise_idx": i,
                }


READERS = {
    "numinamath": read_numinamath,
    "proofnet": read_proofnet,
    "leandojo": read_leandojo_theorems,
}
