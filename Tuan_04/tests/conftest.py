import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mdl.manifest import load_manifest  # noqa: E402
from mdl.staging import build_staging, iter_jsonl, load_corpus_lookups, staging_files  # noqa: E402
from mdl.transform import to_unified  # noqa: E402

SAMPLE_RAW = ROOT / "data_sample" / "raw"
SAMPLE_MANIFEST = ROOT / "data_sample" / "manifest_sample.json"


@pytest.fixture(scope="session")
def staging_sample(tmp_path_factory):
    out = tmp_path_factory.mktemp("staging")
    build_staging(SAMPLE_RAW, out, log=lambda *_: None)
    return out


@pytest.fixture(scope="session")
def manifest():
    return load_manifest(SAMPLE_MANIFEST)


@pytest.fixture(scope="session")
def python_records(staging_sample, manifest):
    code, imports = load_corpus_lookups(staging_sample)
    ctx = {"manifest": manifest, "premise_code": code, "file_imports": imports, "run_id": "test"}
    recs = []
    for src in ("numinamath", "proofnet", "leandojo"):
        recs += [to_unified(s, ctx) for s in iter_jsonl(staging_files(staging_sample, src))]
    return recs


@pytest.fixture(scope="session")
def spark():
    from mdl.spark_etl import spark_session
    s = spark_session(master="local[4]", driver_memory="2g", shuffle_partitions=4, app="mdl-tests")
    yield s
    s.stop()


@pytest.fixture()
def corrupt_staging(staging_sample, tmp_path):
    dst = tmp_path / "staging"
    shutil.copytree(staging_sample, dst)
    f = sorted((dst / "numinamath").glob("*/*.jsonl"))[0]
    first = json.loads(open(f, encoding="utf-8").readline())
    with open(f, "ab") as g:
        g.write(b'{"_source":"numinamath","_key":\n')  # JSON cụt
        g.write(b"[1,2]\n")  # không phải object
        g.write((json.dumps({**first, "_key": "x:1", "problem": ""}) + "\n").encode())  # E03
        g.write((json.dumps(first) + "\n").encode())  # trùng khóa => E06
    return dst
