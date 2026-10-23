"""Kiểm thử lược đồ và hàm ánh xạ tham chiếu (Python)."""
import collections
import json

import pyarrow as pa
import yaml

from mdl.config import SOURCES
from mdl.schema import FIELD_NAMES, PROVENANCE, REQUIRED, arrow_schema
from mdl.transform import LATEX_RE, leandojo_subset, record_id, statement_from_code, validate


def test_contract_matches_schema():
    c = yaml.safe_load(open("docs/data_contract_v1.0.yaml", encoding="utf-8"))
    assert [f["name"] for f in c["fields"]] == FIELD_NAMES
    assert {f["name"] for f in c["fields"] if not f["nullable"]} == set(REQUIRED)


def test_all_sources_present(python_records):
    c = collections.Counter(r["source"] for r in python_records)
    assert set(c) == set(SOURCES) and min(c.values()) >= 100


def test_records_fit_arrow_schema(python_records):
    t = pa.Table.from_pylist([{k: r[k] for k in FIELD_NAMES} for r in python_records], schema=arrow_schema())
    assert t.num_rows == len(python_records)


def test_no_hard_errors_on_sample(python_records):
    assert [validate(r) for r in python_records if validate(r)] == []


def test_provenance_complete(python_records):
    for r in python_records:
        assert all(r[k] is not None for k in PROVENANCE), r["record_id"]
        assert len(r["raw_sha256"]) == 64


def test_record_id_unique_and_stable(python_records):
    ids = [(r["record_id"], r["source_version"]) for r in python_records]
    assert len(ids) == len(set(ids))
    r = python_records[0]
    assert r["record_id"] == record_id(r["source"], r["source_record_key"])


def test_formal_language_by_source(python_records):
    lang = {(r["source"], r["formal_language"]) for r in python_records}
    assert lang == {("numinamath", None), ("proofnet", "lean3"), ("leandojo", "lean4")}


def test_leandojo_join_and_tactics(python_records):
    lean = [r for r in python_records if r["source"] == "leandojo"]
    assert all(r["formal_statement"] for r in lean)  # mẫu được chọn để join đủ
    for r in lean:
        assert r["num_tactics"] == len(r["tactics"])
        assert (r["formal_proof"] is None) == (r["num_tactics"] == 0)
        assert len(r["premises"]) == len(set(r["premises"]))
        assert json.loads(r["extra_json"])["commit"].startswith("29dcec07")


def test_helpers():
    assert statement_from_code("theorem a (x : ℕ) : x = x := by rfl\n") == "theorem a (x : ℕ) : x = x"
    assert statement_from_code("abbrev f := 1") == "abbrev f"
    assert statement_from_code(None) is None
    assert leandojo_subset("Mathlib/Algebra/Group/Basic.lean") == "Mathlib.Algebra"
    assert leandojo_subset(".lake/packages/batteries/Batteries/Data/List.lean") == "batteries"
    assert len(LATEX_RE.findall(r"Cho $x$ và $$y^2$$ với \(z\) và \begin{align}")) == 4


def test_validate_detects_errors():
    bad = {k: None for k in FIELD_NAMES}
    bad.update(record_type="problem_solution", source="numinamath", nl_problem="", nl_solution="x")
    codes = {e.split(":")[0] for e in validate(bad)}
    assert {"E01_MISSING_REQUIRED", "E03_EMPTY_CONTENT"} <= codes


def test_statement_ignores_nested_assign():
    code = "@[to_additive (attr := simp)] theorem foo {x : N} [h : C (a := 1)] : x = x := by rfl"
    assert statement_from_code(code) == "@[to_additive (attr := simp)] theorem foo {x : N} [h : C (a := 1)] : x = x"
    assert statement_from_code("def f (x := 3) : N := x") == "def f (x := 3) : N"
    assert statement_from_code("instance : Foo where\n  x := 1") == "instance : Foo where\n  x"


def test_statement_without_proof_kept_whole():
    code = "@[to_additive (attr := measurability)]\ntheorem t [M G] (hf : A f) :\n    B f"
    assert statement_from_code(code) == code
