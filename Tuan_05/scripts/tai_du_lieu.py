"""Tải snapshot (bỏ qua tệp đã có), giải nén LeanDojo, lập manifest + checksum.

Chạy: python scripts/tai_du_lieu.py [--verify]
"""
import argparse
import json

import _path  # noqa: F401
from mdl.config import RAW
from mdl.manifest import build_manifest, fetch_all, verify

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="manifest/manifest_full.json")
ap.add_argument("--verify", action="store_true", help="chỉ kiểm tra checksum theo manifest có sẵn")
a = ap.parse_args()
if a.verify:
    bad = verify(RAW, a.out)
    print("OK" if not bad else bad)
else:
    fetch_all(RAW)
    m = build_manifest(RAW, a.out)
    (RAW / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(a.out.replace(".json", ".sha256"), "w", encoding="utf-8", newline="\n") as f:
        for e in m["files"]:
            f.write(f"{e['sha256']}  {e['raw_uri']}\n")
    print(f"{len(m['files'])} files, {sum(e['bytes'] for e in m['files']) / 1e9:.2f} GB -> {a.out}")
