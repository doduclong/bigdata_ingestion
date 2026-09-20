"""Lược đồ chung `math_record` v1.0 — nguồn sự thật duy nhất cho data contract, PyArrow và Spark."""
import pyarrow as pa

from .config import SCHEMA_VERSION

# (tên, kiểu, nullable, mô tả). Kiểu: string|int|bool|list<string>
FIELDS = [
    ("record_id", "string", False, "sha1(source + '|' + source_record_key)[:20]; khóa ổn định giữa các lần chạy"),
    ("source", "string", False, "numinamath | proofnet | leandojo (cột partition)"),
    ("source_version", "string", False, "phiên bản snapshot, khớp manifest (cột partition)"),
    ("source_record_key", "string", False, "khóa gốc: id ProofNet / file_path::full_name / shard:row"),
    ("record_type", "string", False, "problem_solution | nl_formal_pair | formal_theorem"),
    ("split", "string", False, "split gốc của nguồn: train/val/valid/test"),
    ("subset", "string", True, "nguồn con (NuminaMath), sách (ProofNet), nhóm module (LeanDojo)"),
    ("nl_problem", "string", True, "đề bài / phát biểu ngôn ngữ tự nhiên (giữ nguyên LaTeX)"),
    ("nl_solution", "string", True, "lời giải / chứng minh ngôn ngữ tự nhiên"),
    ("formal_language", "string", True, "lean3 | lean4 | null"),
    ("formal_statement", "string", True, "phát biểu hình thức (Lean)"),
    ("formal_proof", "string", True, "chứng minh hình thức: các tactic nối bằng xuống dòng"),
    ("formal_header", "string", True, "header/import cần để biên dịch phát biểu"),
    ("formal_goal", "string", True, "goal ban đầu (state_before của tactic đầu tiên)"),
    ("lean_full_name", "string", True, "tên đầy đủ của định lý Lean"),
    ("lean_file_path", "string", True, "đường dẫn tệp .lean trong mathlib4"),
    ("lean_start_line", "int", True, "dòng bắt đầu khai báo"),
    ("lean_end_line", "int", True, "dòng kết thúc khai báo"),
    ("tactics", "list<string>", False, "danh sách tactic (rỗng nếu không có)"),
    ("premises", "list<string>", False, "tên premise duy nhất được dùng trong chứng minh (theo thứ tự xuất hiện)"),
    ("num_tactics", "int", False, "số tactic"),
    ("has_text", "bool", False, "có nl_problem hoặc nl_solution"),
    ("has_latex", "bool", False, "nội dung NL chứa biểu thức LaTeX"),
    ("has_lean", "bool", False, "có formal_statement"),
    ("latex_count", "int", False, "số biểu thức LaTeX trong nl_problem + nl_solution"),
    ("content_sha256", "string", False, "sha256 của nl_problem␟nl_solution␟formal_statement␟formal_proof"),
    ("quality_flags", "list<string>", False, "cảnh báo chất lượng không chặn (W01..)"),
    ("extra_json", "string", True, "trường gốc chưa ánh xạ (JSON), để không mất thông tin"),
    ("raw_uri", "string", False, "đường dẫn tệp raw (tương đối với kho)"),
    ("raw_row", "int", False, "chỉ số dòng/bản ghi trong tệp raw"),
    ("raw_sha256", "string", False, "sha256 tệp raw, khớp manifest"),
    ("license", "string", False, "SPDX id giấy phép của nguồn"),
    ("source_url", "string", False, "URL trang nguồn"),
    ("downloaded_at", "string", False, "thời điểm tải tệp raw (ISO-8601 UTC)"),
    ("ingest_run_id", "string", False, "mã lần chạy ETL tạo ra bản ghi"),
    ("pipeline_version", "string", False, "phiên bản mã pipeline"),
    ("schema_version", "string", False, f"phiên bản lược đồ, hiện tại {SCHEMA_VERSION}"),
]

FIELD_NAMES = [f[0] for f in FIELDS]
REQUIRED = [f[0] for f in FIELDS if not f[2]]
PARTITION_COLS = ["source", "source_version"]
PROVENANCE = ["source", "source_version", "raw_uri", "raw_row", "raw_sha256", "license",
              "source_url", "downloaded_at", "ingest_run_id"]

ENUMS = {
    "source": {"numinamath", "proofnet", "leandojo"},
    "record_type": {"problem_solution", "nl_formal_pair", "formal_theorem"},
    "formal_language": {"lean3", "lean4", None},
}

_PA = {"string": pa.string(), "int": pa.int64(), "bool": pa.bool_(), "list<string>": pa.list_(pa.string())}


def arrow_schema():
    return pa.schema([pa.field(n, _PA[t], nullable=nl) for n, t, nl, _ in FIELDS])
