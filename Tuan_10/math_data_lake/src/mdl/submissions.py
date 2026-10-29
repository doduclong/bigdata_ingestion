"""Nhận một bản ghi, lưu raw/staging và nạp vào kho Parquet bằng Spark."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

import duckdb
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .lake import ingest_batch, new_run_id
from .manifest import load_manifest
from .readers import _meta, _tactics, dumps, nfc
from .spark_etl import spark_session
from .transform import to_unified, validate

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50_000)]
Version = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NuminaData(InputModel):
    source: Text
    problem: Text
    solution: Text


class ProofNetData(InputModel):
    id: Text
    nl_statement: Text
    formal_statement: Text
    nl_proof: str | None = None
    src_header: str | None = None


class Tactic(InputModel):
    tactic: Text
    state_before: str = ""
    state_after: str = ""
    premises: list[Text] = Field(default_factory=list, max_length=1000)


class LeanData(InputModel):
    file_path: Text
    full_name: Text
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    code: Text
    imports: list[Text] = Field(default_factory=list, max_length=1000)
    tactics: list[Tactic] = Field(default_factory=list, max_length=1000)


class Submission(InputModel):
    source_version: Version = "api-v1"
    source_record_key: Annotated[Text, Field(max_length=500)]
    license: Annotated[Text, Field(max_length=100)]
    source_url: Annotated[Text, Field(max_length=2000)]
    split: Literal["train", "val", "valid", "test"] = "train"


class NuminaSubmission(Submission):
    source: Literal["numinamath"]
    data: NuminaData


class ProofNetSubmission(Submission):
    source: Literal["proofnet"]
    split: Literal["valid", "test"] = "test"
    data: ProofNetData


class LeanSubmission(Submission):
    source: Literal["leandojo"]
    data: LeanData


RecordSubmission = Annotated[NuminaSubmission | ProofNetSubmission | LeanSubmission, Field(discriminator="source")]


class SubmissionConflict(ValueError):
    pass


def _prepare(request, raw_uri, run_id, entry):
    data = nfc(request.data.model_dump())
    s = _meta(request.source, request.source_record_key, request.split, raw_uri, 0)
    s["_source_version"] = request.source_version
    lookups = {"premise_code": {}, "file_imports": {}}
    if request.source == "leandojo":
        if request.source_record_key != f"{data['file_path']}::{data['full_name']}":
            raise ValueError("source_record_key phải bằng file_path::full_name đối với LeanDojo")
        if data["end_line"] < data["start_line"]:
            raise ValueError("end_line phải >= start_line")
        traced = [{"tactic": t["tactic"], "state_before": t["state_before"], "state_after": t["state_after"],
                   "annotated_tactic": [t["tactic"], [{"full_name": p} for p in t["premises"]]]}
                  for t in data["tactics"]]
        raw = {**data, "start": [data["start_line"], 0], "end": [data["end_line"], 0], "traced_tactics": traced}
        s.update(file_path=data["file_path"], full_name=data["full_name"], start_line=data["start_line"],
                 end_line=data["end_line"], tactics=_tactics(traced))
        lookups["premise_code"][(data["file_path"], data["full_name"])] = data["code"]
        lookups["file_imports"][data["file_path"]] = data["imports"]
    else:
        raw = data
        s.update(data)
        if request.source == "proofnet" and data["id"] != request.source_record_key:
            raise ValueError("source_record_key phải bằng data.id đối với ProofNet")
    # Giữ cả metadata gửi lên trong raw để kiểm toán được yêu cầu gốc.
    raw["_submission"] = request.model_dump(exclude={"data"})
    ctx = {**lookups, "manifest": {raw_uri: entry}, "run_id": run_id}
    record = to_unified(s, ctx)
    errors = validate(record)
    if errors:
        raise ValueError(", ".join(errors))
    return raw, s, lookups, record


def replay_submissions(raw_root, source):
    """Đưa raw nhận qua API vào các lần dựng lại staging, kể cả bảng phụ LeanDojo."""
    models = {"numinamath": (NuminaSubmission, NuminaData), "proofnet": (ProofNetSubmission, ProofNetData),
              "leandojo": (LeanSubmission, LeanData)}
    model, data_model = models[source]
    for path in sorted((Path(raw_root) / "api" / source).glob("*/*.jsonl")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        req = model(**raw["_submission"], data={k: raw[k] for k in data_model.model_fields if k in raw})
        uri = "raw/" + path.relative_to(raw_root).as_posix()
        _, row, _, _ = _prepare(req, uri, "staging", {"sha256": "pending", "downloaded_at": "pending"})
        yield source, row
        if source == "leandojo":
            meta = {"_source_version": req.source_version, "_raw_uri": uri, "_raw_row": 0}
            yield "leandojo_premise", {**meta, "path": req.data.file_path, "full_name": req.data.full_name,
                                       "code": req.data.code}
            yield "leandojo_file", {**meta, "path": req.data.file_path, "imports": req.data.imports}


def submit_record(request, lake, raw_root, manifest_path):
    """Caller tuần tự hóa các lần ghi. Lưu raw/manifest trước khi công bố Parquet."""
    lake, raw_root, manifest_path = Path(lake), Path(raw_root), Path(manifest_path)
    run_id = new_run_id()
    raw_uri = f"raw/api/{request.source}/{request.source_version}/{run_id}.jsonl"
    entry = {"source": request.source, "source_version": request.source_version, "raw_uri": raw_uri,
             "license": request.license, "source_url": request.source_url, "kind": "api",
             "downloaded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sha256": "pending"}
    raw, staging, _, record = _prepare(request, raw_uri, run_id, entry)
    partition = lake / "math_record" / f"source={request.source}" / f"source_version={request.source_version}"
    if any(partition.glob("*.parquet")):
        with duckdb.connect() as con:
            old = con.execute("SELECT content_sha256 FROM read_parquet(?) WHERE record_id = ?",
                              [str(partition / "*.parquet"), record["record_id"]]).fetchone()
        if old:
            if old[0] != record["content_sha256"]:
                raise SubmissionConflict("Cùng khóa/phiên bản nhưng nội dung khác; dùng source_version mới.")
            return {"status": "unchanged", "record_id": record["record_id"], "source_version": request.source_version,
                    "new": 0, "unchanged": 1}
    body = (dumps(raw) + "\n").encode("utf-8")
    entry.update(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    raw_path = raw_root / raw_uri
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(body)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"].append(entry)
    temp = manifest_path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(manifest_path)
    batch = lake / "_api_batches" / run_id

    def write_part(source, rows):
        path = batch / source / request.source_version / "part-api.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(dumps(row) + "\n" for row in rows), encoding="utf-8")

    write_part(request.source, [staging])
    if request.source == "leandojo":
        data = nfc(request.data.model_dump())
        write_part("leandojo_premise", [{"_source_version": request.source_version,
                                       "path": data["file_path"], "full_name": data["full_name"],
                                       "code": data["code"]}])
        write_part("leandojo_file", [{"_source_version": request.source_version,
                                    "path": data["file_path"], "imports": data["imports"]}])
    from pyspark import SparkContext
    owns_spark = SparkContext._active_spark_context is None
    spark = spark_session(master="local[2]", driver_memory="2g", shuffle_partitions=2, app="mdl-api-ingest")
    try:
        log = ingest_batch(spark, batch, lake, load_manifest(manifest_path), run_id, "API submission",
                           run_compaction=False)
    finally:
        if owns_spark:
            spark.stop()
    stats = log["partitions"].get(f"{request.source}/{request.source_version}", {})
    if log["records_error"] or stats.get("new") != 1:
        raise RuntimeError(f"Không nạp được bản ghi; xem batch {run_id} và bảng errors.")
    return {"status": "created", "record_id": record["record_id"], "source_version": request.source_version,
            "run_id": run_id, "raw_uri": raw_uri, "new": 1, "unchanged": 0}
