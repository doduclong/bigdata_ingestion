"""Sinh data contract (YAML máy đọc + bảng Markdown) từ mdl.schema để tài liệu không lệch với code.

Chạy: python scripts/xuat_data_contract.py
"""
from pathlib import Path

import yaml

import _path  # noqa: F401
from mdl.config import PIPELINE_VERSION, SCHEMA_VERSION, SOURCES
from mdl.schema import ENUMS, FIELDS, PARTITION_COLS, PROVENANCE

contract = {
    "contract": "math_record",
    "version": "1.0",
    "schema_version": SCHEMA_VERSION,
    "pipeline_version": PIPELINE_VERSION,
    "owner": "Nhóm 1 — Math Data Lake (liên hệ: TV1 điều phối, TV7 QA)",
    "status": "release candidate 1.0 (tuần 9) — thay đổi so với 0.1: định dạng row group 16 MB, sắp xếp theo record_id, E07",
    "format": {
        "curated": "Apache Parquet (zstd, row group 16 MB, sắp xếp theo record_id), partition " + "/".join(f"{c}=<..>" for c in PARTITION_COLS),
        "sample": "JSONL UTF-8 + Parquet (data_sample/curated/)",
    },
    "primary_key": ["record_id", "source_version"],
    "partition_columns": PARTITION_COLS,
    "sources": {k: {"version": v["version"], "license": v["license"], "url": v["url"]} for k, v in SOURCES.items()},
    "fields": [
        {"name": n, "type": t, "nullable": nl, "description": d,
         **({"allowed": sorted(x for x in ENUMS[n] if x)} if n in ENUMS else {})}
        for n, t, nl, d in FIELDS
    ],
    "guarantees": [
        "Mọi cột provenance (" + ", ".join(PROVENANCE) + ") khác null trên 100% bản ghi curated.",
        "record_id ổn định: cùng (source, source_record_key) => cùng record_id ở mọi lần chạy và mọi phiên bản.",
        "Không có hai bản ghi trùng (record_id, source_version).",
        "Văn bản đã chuẩn hóa Unicode NFC; LaTeX/Lean giữ nguyên văn, không sửa nội dung.",
        "Split giữ nguyên theo nguồn gốc; Nhóm 1 không tự chia lại split.",
        "Bản ghi vi phạm lỗi cứng (E01–E05) không vào curated mà vào bảng errors kèm mã lỗi.",
    ],
    "quality_flags": {
        "W01_EMPTY_NL_SOLUTION": "cặp NL-formal không có chứng minh NL",
        "W02_FORMAL_STATEMENT_MISSING": "định lý LeanDojo không join được với corpus",
        "W03_REPLACEMENT_CHAR": "có ký tự U+FFFD (mất mã hóa ở nguồn)",
        "W04_CONTROL_CHAR": "có ký tự điều khiển",
        "W05_UNBALANCED_DOLLAR": "số dấu $ lẻ (LaTeX có thể hỏng hoặc là ký hiệu tiền)",
        "W06_VERY_LONG": "trường văn bản dài hơn 50.000 ký tự",
    },
    "error_codes": {
        "E01_MISSING_REQUIRED": "thiếu cột bắt buộc",
        "E02_BAD_ENUM": "giá trị ngoài miền cho phép",
        "E03_EMPTY_CONTENT": "thiếu nội dung tối thiểu theo record_type",
        "E05_PARSE": "dòng staging không phải JSON hợp lệ",
        "E06_DUPLICATE_KEY": "trùng (record_id, source_version) trong một lần nạp",
        "E07_CONTENT_CONFLICT": "nạp gia tăng: cùng khóa, khác nội dung trong cùng source_version (không ghi đè)",
    },
    "versioning": {
        "minor": "thêm cột nullable => tăng schema_version x.y+1, không phá vỡ consumer",
        "major": "đổi tên/xóa/đổi kiểu cột => x+1.0, báo trước 1 tuần, giữ bản cũ song song 1 tuần",
        "data": "snapshot mới => source_version mới, partition mới; bản cũ không bị ghi đè",
    },
    "consumers": {
        "nhom_2_quality": ["record_id", "source", "split", "nl_problem", "nl_solution", "formal_statement",
                           "content_sha256", "raw_uri", "raw_row"],
        "nhom_3_4_retrieval": ["record_id", "lean_full_name", "lean_file_path", "formal_statement", "formal_goal",
                               "premises", "split", "extra_json.split_novel_premises"],
        "nhom_5_autoformalization": ["record_id", "source", "nl_problem", "formal_statement", "formal_language",
                                     "formal_header", "split"],
        "nhom_6_repair": ["record_id", "formal_statement", "formal_header", "formal_language"],
        "nhom_7_proof_search": ["record_id", "lean_full_name", "tactics", "formal_goal", "num_tactics", "premises"],
        "nhom_8_tutor": ["record_id", "subset", "nl_problem", "nl_solution", "has_latex"],
    },
    "access": {
        "sample": "data_sample/curated/math_record_sample.parquet (mock input, 997 bản ghi)",
        "duckdb_example": "SELECT source, count(*) FROM read_parquet('…/source=*/source_version=*/*.parquet', "
                          "hive_partitioning=true) GROUP BY 1",
    },
}

Path("docs").mkdir(exist_ok=True)
Path("docs/data_contract_v1.0.yaml").write_text(
    yaml.safe_dump(contract, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

rows = ["| # | Cột | Kiểu | Null | Mô tả |", "|---|---|---|---|---|"]
for i, (n, t, nl, d) in enumerate(FIELDS, 1):
    allowed = f" Miền: {', '.join(sorted(x for x in ENUMS[n] if x))}." if n in ENUMS else ""
    rows.append(f"| {i} | `{n}` | {t} | {'có' if nl else 'không'} | {d.replace('|', '/')}{allowed} |")
Path("docs/_bang_cot.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
print("docs/data_contract_v1.0.yaml,", len(FIELDS), "fields")
