"""Sinh data dictionary cho bảng math_record: kiểu, null, mô tả, ánh xạ từ 3 nguồn, tỷ lệ null theo nguồn
(đo trên kho đầy đủ nếu có, nếu không thì trên kho mẫu) và một giá trị ví dụ thật.

Chạy (từ thư mục này): python tao_data_dictionary.py  ->  data_dictionary.md, data_dictionary.csv
"""
import csv
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "3_Pipeline_Ingest_ETL" / "src"))
from mdl.config import STORAGE  # noqa: E402
from mdl.schema import ENUMS, FIELDS, PARTITION_COLS, PROVENANCE  # noqa: E402

# Ánh xạ trường nguồn -> cột chung (khớp transform.to_unified)
MAP = {
    "record_id": ("sha1('numinamath|'+key)[:20]", "sha1('proofnet|'+id)[:20]", "sha1('leandojo|'+file_path::full_name)[:20]"),
    "source_record_key": ("<shard>:<row> (không có ID gốc)", "id", "file_path::full_name"),
    "split": ("tên tệp: train/test", "valid/test", "random split: train/val/test"),
    "subset": ("source (cn_k12, olympiads…)", "tên sách trong id (phần trước |)", "2 cấp module (Mathlib.Algebra) / gói .lake"),
    "nl_problem": ("problem", "nl_statement", "—"),
    "nl_solution": ("solution", "nl_proof", "—"),
    "formal_language": ("—", "lean3", "lean4"),
    "formal_statement": ("—", "formal_statement", "corpus.code cắt tại := mức ngoặc 0"),
    "formal_proof": ("—", "—", "các tactic nối bằng xuống dòng"),
    "formal_header": ("—", "src_header", "corpus.imports nối bằng xuống dòng"),
    "formal_goal": ("—", "—", "traced_tactics[0].state_before"),
    "lean_full_name": ("—", "—", "full_name"),
    "lean_file_path": ("—", "—", "file_path"),
    "lean_start_line": ("—", "—", "start[0]"),
    "lean_end_line": ("—", "—", "end[0]"),
    "tactics": ("[]", "[]", "traced_tactics[].tactic"),
    "premises": ("[]", "[]", "annotated_tactic[1][].full_name (duy nhất, theo thứ tự)"),
    "extra_json": ("messages nếu khác problem/solution", "—", "url, commit, start, end, split_novel_premises"),
}
DERIVED = {"num_tactics", "has_text", "has_latex", "has_lean", "latex_count", "content_sha256", "quality_flags"}

full = STORAGE / "lake" / "math_record"
lake = full if full.exists() else HERE.parent / "1_KhoParquetMau_Manifest" / "kho_mau" / "math_record"
src = f"read_parquet('{lake.as_posix()}/**/*.parquet', hive_partitioning=true)"
con = duckdb.connect()
con.execute("SET memory_limit='1GB'; SET threads=4")
total = con.execute(f"SELECT count(*) FROM {src}").fetchone()[0]

rows = []
for name, typ, nullable, desc in FIELDS:
    null_by_src = con.execute(f"SELECT source, round(100.0 * avg(CASE WHEN {name} IS NULL THEN 1 ELSE 0 END), 2) "
                              f"FROM {src} GROUP BY 1 ORDER BY 1").fetchall()
    ex = con.execute(f"SELECT CAST({name} AS VARCHAR) FROM {src} WHERE {name} IS NOT NULL "
                     f"ORDER BY record_id LIMIT 1").fetchone()
    example = (ex[0] if ex else "").replace("\n", " ").replace("|", "/")
    if name in PROVENANCE:
        group = "provenance"
    elif name in DERIVED:
        group = "dẫn xuất"
    elif name in ("record_id", "source", "source_version", "source_record_key", "record_type", "split", "subset"):
        group = "định danh"
    else:
        group = "nội dung"
    m = MAP.get(name, ("(sinh bởi pipeline)",) * 3 if group in ("dẫn xuất", "provenance") else ("—",) * 3)
    rows.append({
        "cot": name, "nhom": group, "kieu": typ, "null": "có" if nullable else "không",
        "partition": "có" if name in PARTITION_COLS else "",
        "mien_gia_tri": ", ".join(sorted(v for v in ENUMS[name] if v)) if name in ENUMS else "",
        "mo_ta": desc, "numinamath": m[0], "proofnet": m[1], "leandojo": m[2],
        "ty_le_null_%": "; ".join(f"{s}: {p}" for s, p in null_by_src),
        "vi_du": example[:90] + ("…" if len(example) > 90 else ""),
    })

with open(HERE / "data_dictionary.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

md = [f"# Data dictionary — bảng `math_record` (lược đồ 1.0)", "",
      f"Sinh tự động bởi `tao_data_dictionary.py` từ `mdl.schema` và kho `{('đầy đủ' if lake == full else 'mẫu')}` "
      f"({total:,} bản ghi). Khóa chính `(record_id, source_version)`; partition `source/source_version`.", "",
      "## 1. Từ điển cột", "",
      "| # | Cột | Nhóm | Kiểu | Null | Mô tả | Tỷ lệ null % theo nguồn | Ví dụ |", "|---|---|---|---|---|---|---|---|"]
for i, r in enumerate(rows, 1):
    dom = f" Miền: {r['mien_gia_tri']}." if r["mien_gia_tri"] else ""
    md.append(f"| {i} | `{r['cot']}` | {r['nhom']} | {r['kieu']} | {r['null']} | {r['mo_ta'].replace('|', '/')}{dom} | "
              f"{r['ty_le_null_%']} | `{r['vi_du']}` |")
md += ["", "## 2. Ánh xạ trường nguồn → cột chung", "", "| Cột | NuminaMath-CoT | ProofNet | LeanDojo Benchmark 4 |",
       "|---|---|---|---|"]
for r in rows:
    if r["cot"] in MAP:
        md.append(f"| `{r['cot']}` | {r['numinamath']} | {r['proofnet']} | {r['leandojo']} |")
md += ["", "Cột nhóm *dẫn xuất* và *provenance* do pipeline sinh (xem `data_contract.md`)."]
(HERE / "data_dictionary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"{len(rows)} cột, kho: {lake} ({total} bản ghi)")
