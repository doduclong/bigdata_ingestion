"""Ánh xạ bản ghi staging -> lược đồ chung `math_record` (bản tham chiếu bằng Python thuần).

Spark ETL (tuần 4) phải cho kết quả giống hệt hàm này trên mọi cột nội dung (kiểm bằng test parity).
"""
import hashlib
import re

from .config import PIPELINE_VERSION, RECORD_TYPES, SCHEMA_VERSION, SOURCES
from .schema import ENUMS, REQUIRED

LATEX_RE = re.compile(r"\$\$.+?\$\$|\$[^$]+?\$|\\\(.+?\\\)|\\\[.+?\\\]|\\begin\{", re.S)
DOLLAR_RE = re.compile(r"(?<!\\)\$")
CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
TRAIL_WS = re.compile(r"[ \t\r\n]+$")


def _bracket_content(depth):
    """Nội dung trong ngoặc, cho phép lồng `depth` tầng; dùng nhóm nguyên tử (?>...) để không quay lui."""
    if depth == 0:
        return r"(?>[^()\[\]{}]*)"
    i = _bracket_content(depth - 1)
    return r"(?>(?>[^()\[\]{}]+)|\(" + i + r"\)|\[" + i + r"\]|\{" + i + r"\})*"


_I = _bracket_content(3)
# Phần đầu khai báo tới ':=' đầu tiên Ở MỨC NGOẶC 0 (bỏ qua ':=' trong @[attr (x := y)] hay tham số mặc định).
# Cú pháp dùng chung cho Python re và Java regex (Spark) => cùng kết quả.
STMT_PATTERN = r"(?s)^((?>(?>[^()\[\]{}:]+)|:(?!=)|\(" + _I + r"\)|\[" + _I + r"\]|\{" + _I + r"\})*):="
STMT_RE = re.compile(STMT_PATTERN)
MAX_LEN = 50_000


def record_id(source, key):
    return hashlib.sha1(f"{source}|{key}".encode("utf-8")).hexdigest()[:20]


def content_sha256(r):
    parts = [r.get(k) or "" for k in ("nl_problem", "nl_solution", "formal_statement", "formal_proof")]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def leandojo_subset(file_path):
    parts = file_path.split("/")
    if parts[0] == ".lake" and len(parts) > 2:
        return parts[2]
    return ".".join(parts[:2])


def statement_from_code(code):
    if code is None:
        return None
    m = STMT_RE.match(code)
    head = m.group(1) if m else code  # không có ":=" ở mức 0: corpus chỉ lưu phát biểu, giữ nguyên
    return TRAIL_WS.sub("", head)


def quality_flags(r):
    flags = []
    if r["record_type"] == "nl_formal_pair" and not r["nl_solution"]:
        flags.append("W01_EMPTY_NL_SOLUTION")
    if r["record_type"] == "formal_theorem" and r["formal_statement"] is None:
        flags.append("W02_FORMAL_STATEMENT_MISSING")
    texts = [r[k] for k in ("nl_problem", "nl_solution", "formal_statement", "formal_proof", "formal_goal") if r[k]]
    if any("�" in t for t in texts):
        flags.append("W03_REPLACEMENT_CHAR")
    if any(CTRL_RE.search(t) for t in texts):
        flags.append("W04_CONTROL_CHAR")
    if any(len(DOLLAR_RE.findall(r[k])) % 2 for k in ("nl_problem", "nl_solution") if r[k]):
        flags.append("W05_UNBALANCED_DOLLAR")
    if any(len(t) > MAX_LEN for t in texts):
        flags.append("W06_VERY_LONG")
    return flags


def to_unified(s, ctx):
    """s: bản ghi staging; ctx: {'manifest': {raw_uri: entry}, 'premise_code': {(path, name): code},
    'file_imports': {path: [..]}, 'run_id': str}."""
    src = s["_source"]
    spec = SOURCES[src]
    r = dict.fromkeys(("subset", "nl_problem", "nl_solution", "formal_language", "formal_statement",
                       "formal_proof", "formal_header", "formal_goal", "lean_full_name", "lean_file_path",
                       "lean_start_line", "lean_end_line"))
    r.update(record_id=record_id(src, s["_key"]), source=src, source_version=s["_source_version"],
             source_record_key=s["_key"], record_type=RECORD_TYPES[src], split=s["_split"],
             tactics=[], premises=[])
    if src == "numinamath":
        r.update(subset=s.get("source"), nl_problem=s.get("problem"), nl_solution=s.get("solution"))
    elif src == "proofnet":
        r.update(subset=s["id"].split("|")[0], nl_problem=s.get("nl_statement"), nl_solution=s.get("nl_proof"),
                 formal_language="lean3", formal_statement=s.get("formal_statement"),
                 formal_header=s.get("src_header"))
    else:
        tac = s.get("tactics") or []
        code = ctx.get("premise_code", {}).get((s["file_path"], s["full_name"]))
        imports = ctx.get("file_imports", {}).get(s["file_path"])
        prem = []
        for t in tac:
            for p in t.get("premises") or []:
                if p not in prem:
                    prem.append(p)
        r.update(subset=leandojo_subset(s["file_path"]), formal_language="lean4",
                 formal_statement=statement_from_code(code),
                 formal_proof="\n".join(t["tactic"] for t in tac) if tac else None,
                 formal_header="\n".join(imports) if imports else None,
                 formal_goal=tac[0].get("state_before") if tac else None,
                 lean_full_name=s["full_name"], lean_file_path=s["file_path"],
                 lean_start_line=s.get("start_line"), lean_end_line=s.get("end_line"),
                 tactics=[t["tactic"] for t in tac], premises=prem)
    nl = [r["nl_problem"], r["nl_solution"]]
    r["num_tactics"] = len(r["tactics"])
    r["latex_count"] = sum(len(LATEX_RE.findall(t)) for t in nl if t)
    r["has_text"] = any(bool(t) for t in nl)
    r["has_latex"] = r["latex_count"] > 0
    r["has_lean"] = r["formal_statement"] is not None
    r["content_sha256"] = content_sha256(r)
    r["quality_flags"] = quality_flags(r)
    r["extra_json"] = s.get("_extra")
    m = ctx.get("manifest", {}).get(s["_raw_uri"], {})
    r.update(raw_uri=s["_raw_uri"], raw_row=s["_raw_row"], raw_sha256=m.get("sha256"), license=spec["license"],
             source_url=spec["url"], downloaded_at=m.get("downloaded_at"), ingest_run_id=ctx.get("run_id"),
             pipeline_version=PIPELINE_VERSION, schema_version=SCHEMA_VERSION)
    return r


def validate(r):
    """Trả về danh sách mã lỗi cứng (rỗng = hợp lệ). Bản ghi lỗi đi vào bảng quarantine."""
    errs = []
    missing = [k for k in REQUIRED if r.get(k) is None]
    if missing:
        errs.append("E01_MISSING_REQUIRED:" + ",".join(missing))
    for k, allowed in ENUMS.items():
        if r.get(k) not in allowed:
            errs.append(f"E02_BAD_ENUM:{k}")
    t = r.get("record_type")
    if t == "problem_solution" and not (r.get("nl_problem") and r.get("nl_solution")):
        errs.append("E03_EMPTY_CONTENT")
    elif t == "nl_formal_pair" and not (r.get("nl_problem") and r.get("formal_statement")):
        errs.append("E03_EMPTY_CONTENT")
    elif t == "formal_theorem" and not r.get("lean_full_name"):
        errs.append("E03_EMPTY_CONTENT")
    return errs
