"""Vẽ sơ đồ lược đồ v0.1 và sơ đồ kiến trúc nháp (Tuần 1). Chạy: python scripts/ve_so_do.py"""
import os

import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Segoe UI"
from matplotlib.patches import FancyBboxPatch

os.makedirs("hinh", exist_ok=True)


def box(ax, x, y, w, h, title, lines, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=color, ec="#333", lw=1.2))
    ax.text(x + w / 2, y + h - 0.035, title, ha="center", va="top", fontsize=10, weight="bold")
    for i, t in enumerate(lines):
        ax.text(x + 0.015, y + h - 0.085 - i * 0.032, t, ha="left", va="top", fontsize=7.6, family="Consolas")


def arrow(ax, x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.3, color="#444"))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.015, label, ha="center", fontsize=7.5, color="#444")


# 1) Sơ đồ lược đồ v0.1: 3 nguồn -> bảng math_record
fig, ax = plt.subplots(figsize=(13, 7.5))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
box(ax, 0.01, 0.70, 0.27, 0.27, "NuminaMath-CoT (Parquet)", [
    "source      : str (cn_k12, olympiads..)", "problem     : str (text+LaTeX)", "solution    : str (CoT, LaTeX)",
    "messages    : list<role,content>", "(không có id gốc -> shard:row)"], "#E8F1FB")
box(ax, 0.01, 0.38, 0.27, 0.27, "ProofNet (JSONL, Lean 3)", [
    "id             : 'Rudin|exercise_1_1b'", "nl_statement   : str (LaTeX)", "nl_proof       : str (LaTeX)",
    "formal_statement: str (Lean 3)", "src_header     : str (import/open)"], "#EAF7EA")
box(ax, 0.01, 0.02, 0.27, 0.32, "LeanDojo Benchmark 4 (JSON)", [
    "url, commit (mathlib4)", "file_path, full_name", "start, end : [line, col]",
    "traced_tactics: list<tactic,", "  annotated_tactic, state_before,", "  state_after>",
    "+ corpus.jsonl: path, imports,", "  premises<full_name, code, kind>"], "#FDF1E3")
box(ax, 0.43, 0.02, 0.56, 0.95, "curated.math_record  (lược đồ chung v0.1)", [
    "-- định danh ---------------------------------------------",
    "record_id          str   sha1(source|source_record_key)[:20]",
    "source             str   numinamath|proofnet|leandojo   [P]",
    "source_version     str   hf-<sha>|git-<sha>|v10-<commit> [P]",
    "source_record_key  str   khóa gốc (id / file::name / shard:row)",
    "record_type        str   problem_solution|nl_formal_pair|formal_theorem",
    "split, subset      str   train/val/test ; chủ đề/nguồn con",
    "-- nội dung ----------------------------------------------",
    "nl_problem, nl_solution         str  (text + LaTeX)",
    "formal_language                 str  lean3|lean4|null",
    "formal_statement, formal_proof  str",
    "formal_header, formal_goal      str",
    "lean_full_name, lean_file_path  str",
    "lean_start_line, lean_end_line  int",
    "tactics            list<str> ; premises list<str>",
    "has_text, has_latex, has_lean   bool ; latex_count int",
    "content_sha256     str   băm nội dung chuẩn hóa",
    "extra_json         str   trường gốc chưa ánh xạ (không mất)",
    "-- provenance (bắt buộc, không được null) ----------------",
    "raw_uri, raw_sha256, raw_row    vị trí bản ghi trong vùng raw",
    "license, source_url, downloaded_at",
    "ingest_run_id, pipeline_version, ingested_at, schema_version",
    "", "[P] = cột partition ở vùng curated (Parquet)"], "#F4F4F4")
arrow(ax, 0.29, 0.83, 0.43, 0.75, "problem->nl_problem")
arrow(ax, 0.29, 0.51, 0.43, 0.55, "nl_statement->nl_problem")
arrow(ax, 0.29, 0.18, 0.43, 0.35, "join corpus -> formal_statement")
ax.set_title("Sơ đồ lược đồ v0.1 - Nhóm 1 Math Data Lake", fontsize=13, weight="bold")
fig.savefig("hinh/so_do_luoc_do_v0.1.png", dpi=150, bbox_inches="tight")

# 2) Kiến trúc nháp các vùng dữ liệu
fig, ax = plt.subplots(figsize=(13, 3.6))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
stages = [
    ("Nguồn", ["HF NuminaMath", "GitHub ProofNet", "Zenodo LeanDojo"], "#E8F1FB"),
    ("Raw zone", ["tệp gốc bất biến", "manifest + sha256", "ngày tải, license"], "#FDF1E3"),
    ("Staging", ["JSONL UTF-8/NFC", "snake_case", "_src_file,_src_row"], "#EAF7EA"),
    ("ETL", ["Baseline: Python", "  tuần tự -> JSONL", "Chính: Spark ETL"], "#FBE8EF"),
    ("Curated", ["Parquet", "partition source/", "  source_version"], "#F4F4F4"),
    ("Catalog/API", ["data card", "DuckDB queries", "data contract"], "#EFEAFB"),
]
w, gap = 0.14, 0.025
for i, (t, ls, c) in enumerate(stages):
    x = 0.01 + i * (w + gap)
    box(ax, x, 0.12, w, 0.75, t, ls, c)
    if i:
        arrow(ax, x - gap, 0.5, x, 0.5)
ax.text(0.5, 0.02, "Bảng lỗi (quarantine) + thống kê lỗi được ghi ở mỗi bước ETL", ha="center", fontsize=9, style="italic")
fig.savefig("hinh/kien_truc_v0.1.png", dpi=150, bbox_inches="tight")
print("saved hinh/so_do_luoc_do_v0.1.png, hinh/kien_truc_v0.1.png")
