"""Phân tích lỗi tuần 8: phân loại cờ chất lượng theo nguyên nhân (quy tắc regex), đếm và lấy ví dụ.

Đầu vào: kho tuần 6 (_storage/lake_w6). Kết quả: results/raw/error_analysis.json, results/tables/error_taxonomy.csv
"""
import json

import duckdb

import _path  # noqa: F401
from mdl.config import STORAGE
from mdl.report import write_csv

T = f"read_parquet('{(STORAGE / 'lake_w6' / 'math_record').as_posix()}/**/*.parquet', hive_partitioning=true)"
con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET threads=4")
txt = "coalesce(nl_problem, '') || ' ' || coalesce(nl_solution, '')"

# W05: số dấu $ lẻ — phân loại theo dấu hiệu
w05 = f"""SELECT record_id, subset, {txt} AS t FROM {T} WHERE list_contains(quality_flags, 'W05_UNBALANCED_DOLLAR')"""
cats_w05 = {
    "W05a_ky_hieu_tien_te": r"\$\s?[0-9]",  # "$5", "$ 1,200" (RE2 của DuckDB không có lookahead)
    "W05b_dollar_thoat_\\$": r"\\\$",
    "W05c_display_$$_le": r"\$\$",
}
# W04: ký tự điều khiển — phân loại theo ký tự và ngữ cảnh
w04 = f"""SELECT record_id, subset, {txt} AS t FROM {T} WHERE list_contains(quality_flags, 'W04_CONTROL_CHAR')"""
cats_w04 = {  # kiểm tra ví dụ: 0x0B/0x0C nằm đúng chỗ "ff"/"fi" => mã ligature font TeX OT1 sót lại khi trích PDF
    "W04a_0x0C_ligature_fi_OT1": "\x0c",
    "W04b_0x0B_ligature_ff_OT1": "\x0b",
    "W04c_0x08_loi_escape_backslash_b(oxed)": "\x08",
    "W04d_ky_tu_dieu_khien_khac": "[\x00-\x07\x0e-\x1f\x7f]",
}
res = {"W05": {}, "W04": {}}
rows = []
for flag, q, cats in (("W05", w05, cats_w05), ("W04", w04, cats_w04)):
    total = con.execute(f"SELECT count(*) FROM ({q})").fetchone()[0]
    res[flag]["total"] = total
    excl = []  # các mẫu đã dùng => phần "không khớp quy tắc"
    for cat, pat in cats.items():
        n = con.execute(f"SELECT count(*) FROM ({q}) WHERE regexp_matches(t, ?)", [pat]).fetchone()[0]
        ex = con.execute(f"SELECT record_id, subset, substr(regexp_extract(t, ?), 1, 120) FROM ({q}) "
                         "WHERE regexp_matches(t, ?) ORDER BY record_id LIMIT 3",
                         [".{0,40}(" + pat + ").{0,40}", pat]).fetchall()
        by_subset = con.execute(f"SELECT subset, count(*) FROM ({q}) WHERE regexp_matches(t, ?) GROUP BY 1 "
                                "ORDER BY 2 DESC LIMIT 4", [pat]).fetchall()
        res[flag][cat] = {"count": n, "examples": ex, "by_subset": by_subset}
        rows.append({"flag": flag, "category": cat, "count": n, "share_of_flag": round(n / total, 4) if total else 0,
                     "top_subsets": "; ".join(f"{s}:{c}" for s, c in by_subset)})
        excl.append(pat)
    cond = " AND ".join("NOT regexp_matches(t, ?)" for _ in excl)
    n = con.execute(f"SELECT count(*) FROM ({q}) WHERE {cond}", excl).fetchone()[0]
    ex = con.execute(f"SELECT record_id, subset, substr(t, 1, 160) FROM ({q}) WHERE {cond} ORDER BY record_id LIMIT 5",
                     excl).fetchall()
    res[flag]["khong_khop_quy_tac"] = {"count": n, "examples": ex}
    rows.append({"flag": flag, "category": "khong_khop_quy_tac", "count": n,
                 "share_of_flag": round(n / total, 4) if total else 0, "top_subsets": ""})

# W03 (U+FFFD) và lỗi cứng: liệt kê đầy đủ vì số lượng nhỏ
res["W03"] = con.execute(f"SELECT record_id, subset, regexp_extract({txt}, '.{{0,30}}�.{{0,30}}') FROM {T} "
                         "WHERE list_contains(quality_flags, 'W03_REPLACEMENT_CHAR')").fetchall()
res["E_errors"] = con.execute(f"SELECT source, raw_uri, raw_row, errors FROM read_json('"
                              f"{(STORAGE / 'lake_w6' / 'errors').as_posix()}/*.json', format='newline_delimited') "
                              "ORDER BY raw_row").fetchall()
# Trùng nội dung chính xác (gợi ý cho Nhóm 2)
res["exact_duplicates"] = con.execute(f"""SELECT source, count(*) AS records_in_dup_groups, count(DISTINCT content_sha256)
    AS groups FROM (SELECT source, content_sha256, count(*) OVER (PARTITION BY content_sha256) c FROM {T}) WHERE c > 1
    GROUP BY 1""").fetchall()
open("results/raw/error_analysis.json", "w", encoding="utf-8").write(
    json.dumps(res, ensure_ascii=False, indent=1, default=str))
write_csv(rows, "results/tables/error_taxonomy.csv")
for r in rows:
    print(r)
print("W03", len(res["W03"]), "E", len(res["E_errors"]), "dup", res["exact_duplicates"])
