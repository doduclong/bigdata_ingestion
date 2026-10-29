"""Kiểm tra POST thật với Spark, kho/raw/manifest tạm; không ghi vào dữ liệu đang dùng."""
import json

import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient

from mdl.manifest import build_manifest, load_manifest
from mdl.staging import build_staging, iter_jsonl, load_corpus_lookups, staging_files
from mdl.transform import to_unified
from conftest import ROOT


@pytest.fixture
def write_client(tmp_path, monkeypatch):
    import mdl.api as api
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"files": []}), encoding="utf-8")
    monkeypatch.setattr(api, "LAKE", tmp_path / "lake")
    monkeypatch.setattr(api, "RAW_ROOT", tmp_path)
    monkeypatch.setattr(api, "MANIFEST", manifest_path)
    monkeypatch.setattr(api, "_con", None)
    monkeypatch.setattr(api, "_catalog", None)
    with TestClient(api.app) as client:
        yield client, tmp_path


def test_create_retry_conflict_and_provenance(write_client):
    client, root = write_client
    payload = json.loads((ROOT / "data_sample/api_record_test.json").read_text(encoding="utf-8"))
    response = client.post("/records", json=payload)
    assert response.status_code == 201, response.text
    result = response.json()
    rid = result["record_id"]
    assert result["new"] == 1 and (root / result["raw_uri"]).is_file()
    assert client.get("/health").json()["records"] == 1
    record = client.get(f"/records/{rid}").json()
    assert record["nl_problem"] == "test" and record["license"] == "CC0-1.0"
    assert record["source_url"] == payload["source_url"]
    assert client.get(f"/provenance/{rid}").json()["ok"] is True
    assert client.get("/catalog").json()["tables"][0]["partitions"][0]["license"] == "CC0-1.0"
    retry = client.post("/records", json=payload)
    assert retry.status_code == 200 and retry.json()["unchanged"] == 1
    payload["data"]["solution"] = "different"
    assert client.post("/records", json=payload).status_code == 409
    assert client.get("/health").json()["records"] == 1
    # Làm mới manifest không làm mất nguồn gốc của raw được nhận qua API.
    rebuilt = build_manifest(root / "raw")
    assert rebuilt["files"][0]["sha256"] == record["raw_sha256"]
    assert len(list((root / "lake/_lake_log").glob("*.json"))) == 1
    # Sau khi đã đọc/cache API, thêm một bản ghi nữa phải hiện ngay ở GET/catalog.
    payload["source_record_key"] = "api-test-002"
    assert client.post("/records", json=payload).status_code == 201
    assert client.get("/health").json()["records"] == 2
    assert client.get("/catalog").json()["tables"][0]["rows"] == 2
    build_staging(root / "raw", root / "replayed", sources=("numinamath",), log=lambda *_: None)
    replayed = list(iter_jsonl(staging_files(root / "replayed", "numinamath")))
    assert len(replayed) == 2 and {r["_source_version"] for r in replayed} == {"api-v1"}


@pytest.mark.parametrize("source,data,key,split", [
    ("proofnet", {"id": "test|001", "nl_statement": "test", "formal_statement": "example : True := trivial"},
     "test|001", "test"),
    ("leandojo", {"file_path": "Test.lean", "full_name": "test_api", "start_line": 1, "end_line": 2,
                  "code": "theorem test_api : True := by trivial",
                  "imports": ["import Mathlib"], "tactics": [{"tactic": "trivial", "state_before": "⊢ True"}]},
     "Test.lean::test_api", "train"),
])
def test_other_sources(write_client, source, data, key, split):
    client, root = write_client
    payload = {"source": source, "data": data, "source_record_key": key, "split": split,
               "license": "CC0-1.0", "source_url": "https://example.org/test"}
    r = client.post("/records", json=payload)
    assert r.status_code == 201, r.text
    rid = r.json()["record_id"]
    assert client.get(f"/records/{rid}").json()["has_lean"] is True
    assert client.get(f"/provenance/{rid}").json()["ok"] is True
    assert sum(pq.read_metadata(p).num_rows for p in (root / "lake/math_record").rglob("*.parquet")) == 1
    build_staging(root / "raw", root / "replayed", sources=(source,), log=lambda *_: None)
    assert len(list(iter_jsonl(staging_files(root / "replayed", source)))) == 1
    if source == "leandojo":
        payload["source_version"] = "api-v2"
        payload["data"]["code"] = "theorem test_api : 1 = 1 := by rfl"
        assert client.post("/records", json=payload).status_code == 201
        assert client.get(f"/records/{rid}").status_code == 409
        assert client.get(f"/records/{rid}", params={"source_version": "api-v2"}).json()["formal_statement"] == \
            "theorem test_api : 1 = 1"
        assert client.get(f"/provenance/{rid}", params={"source_version": "api-v1"}).json()["ok"] is True
        build_staging(root / "raw", root / "replayed", sources=(source,), log=lambda *_: None)
        code, imports = load_corpus_lookups(root / "replayed")
        ctx = {"manifest": load_manifest(root / "manifest.json"), "premise_code": code,
               "file_imports": imports, "run_id": "replay"}
        replayed = [to_unified(s, ctx) for s in iter_jsonl(staging_files(root / "replayed", source))]
        assert {r["source_version"]: r["formal_statement"] for r in replayed} == {
            "api-v1": "theorem test_api : True", "api-v2": "theorem test_api : 1 = 1"}


def test_invalid_input_writes_nothing(write_client):
    client, root = write_client
    payload = json.loads((ROOT / "data_sample/api_record_test.json").read_text(encoding="utf-8"))
    payload["data"]["solution"] = " "
    assert client.post("/records", json=payload).status_code == 422
    payload["source_version"] = "../../escape"
    assert client.post("/records", json=payload).status_code == 422
    assert not (root / "raw").exists()
