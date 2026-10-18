"""Đo độ tin cậy của heuristic tách formal_statement (cắt tại ':=' đầu tiên) trên toàn bộ LeanDojo.

Dấu hiệu cắt sai: ngoặc (), [], {} không cân bằng trong phần phát biểu. Kết quả: results/raw/formal_statement_check.json
"""
import json

import duckdb

import _path  # noqa: F401
from mdl.config import STORAGE

p = (STORAGE / "out" / "spark" / "full" / "math_record").as_posix()
con = duckdb.connect()
con.execute("SET memory_limit='2GB'; SET threads=4")
bal = " AND ".join(f"length(formal_statement) - length(replace(formal_statement, '{o}', '')) = "
                   f"length(formal_statement) - length(replace(formal_statement, '{c}', ''))"
                   for o, c in [("(", ")"), ("[", "]"), ("{", "}")])
q = f"""SELECT count(*) AS n,
  sum(CASE WHEN {bal} THEN 0 ELSE 1 END) AS unbalanced,
  sum(CASE WHEN regexp_matches(formal_statement, '^(@\[|/--|theorem|lemma|protected|private|nonrec|instance|def|abbrev|noncomputable|irreducible_def|alias|example)') THEN 1 ELSE 0 END) AS starts_with_keyword
FROM read_parquet('{p}/source=leandojo/**/*.parquet')"""
n, unbalanced, kw = con.execute(q).fetchone()
examples = con.execute(f"SELECT lean_full_name, substr(formal_statement, 1, 160) FROM read_parquet("
                       f"'{p}/source=leandojo/**/*.parquet') WHERE NOT ({bal}) ORDER BY 1 LIMIT 5").fetchall()
res = {"leandojo_records": n, "unbalanced_brackets": unbalanced, "unbalanced_rate": round(unbalanced / n, 5),
       "starts_with_decl_keyword": kw, "examples_unbalanced": examples}
open("results/raw/formal_statement_check.json", "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False,
                                                                                       indent=2))
print(json.dumps(res, ensure_ascii=False, indent=1))
