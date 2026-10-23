"""Kiểm thử API dữ liệu trên kho dựng từ bản mẫu (FastAPI TestClient)."""
import pytest
from fastapi.testclient import TestClient

from mdl.lake import ingest_batch

from conftest import ROOT, SAMPLE_MANIFEST


@pytest.fixture(scope="module")
def client(spark, staging_sample, manifest, tmp_path_factory):
    lake = tmp_path_factory.mktemp("api_lake")
    ingest_batch(spark, staging_sample, lake, manifest, "api", "mẫu")
    import mdl.api as api
    api.LAKE, api.MANIFEST, api.RAW_ROOT, api._con, api._catalog = lake, SAMPLE_MANIFEST, ROOT / "data_sample", None, None
    return TestClient(api.app)


def test_health_and_stats(client):
    assert client.get("/health").json()["records"] == 997
    stats = client.get("/stats").json()
    assert sum(r["records"] for r in stats) == 997


def test_record_lookup_and_validation(client):
    first = client.get("/records", params={"limit": 1}).json()["records"][0]
    r = client.get(f"/records/{first['record_id']}").json()
    assert r["record_id"] == first["record_id"] and r["raw_sha256"]
    assert client.get("/records/00000000000000000000").status_code == 404
    assert client.get("/records/not-an-id").status_code == 422  # chặn đầu vào sai dạng
    assert client.get("/records", params={"fields": "record_id,drop table"}).status_code == 400


def test_keyset_pagination_covers_all(client):
    seen, after = [], None
    while True:
        page = client.get("/records", params={"limit": 200, "fields": "record_id",
                                              **({"after": after} if after else {})}).json()
        seen += [r["record_id"] for r in page["records"]]
        after = page["next_after"]
        if not after:
            break
    assert len(seen) == len(set(seen)) == 997 and seen == sorted(seen)


def test_group_endpoints(client):
    pairs = client.get("/pairs/nl-formal", params={"split": "test"}).json()
    assert len(pairs) == 100 and all(p["formal_language"] == "lean3" for p in pairs)
    lean = client.get("/records", params={"source": "leandojo", "limit": 1, "fields": "premises"}).json()
    prem = next(p for r in client.get("/records", params={"source": "leandojo", "limit": 300,
                                                            "fields": "record_id,premises"}).json()["records"]
                for p in r["premises"])
    assert client.get(f"/premises/{prem}/theorems").json()
    assert lean["count"] == 1


def test_provenance_and_export(client, tmp_path):
    rid = client.get("/records", params={"source": "proofnet", "limit": 1}).json()["records"][0]["record_id"]
    t = client.get(f"/provenance/{rid}").json()
    assert t["fields_mismatch"] == []
    r = client.get("/export", params={"source": "proofnet", "split": "valid"})
    assert r.status_code == 200
    p = tmp_path / "x.parquet"
    p.write_bytes(r.content)
    import pyarrow.parquet as pq
    assert pq.read_metadata(p).num_rows == 100
    assert client.get("/catalog").json()["tables"][0]["rows"] == 997
