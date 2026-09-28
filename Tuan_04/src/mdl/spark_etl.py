"""Spark ETL: staging JSONL -> curated Parquet (partition source/source_version) + bảng lỗi.

Toàn bộ phép biến đổi dùng biểu thức Spark SQL gốc (chạy trong JVM, không UDF Python) và phải cho kết quả
giống `transform.to_unified` trên mọi cột nội dung — được kiểm bằng tests/test_parity.py.
"""
import os
import sys
import time
from pathlib import Path

from .config import PIPELINE_VERSION, SCHEMA_VERSION, SOURCES, STORAGE
from .schema import ENUMS, FIELD_NAMES, PARTITION_COLS, REQUIRED
from .transform import STMT_PATTERN

LATEX_JAVA = r"(?s)\$\$.+?\$\$|\$[^$]+?\$|\\\(.+?\\\)|\\\[.+?\\\]|\\begin\{"
DOLLAR_JAVA = r"(?<!\\)\$"
CTRL_JAVA = r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
MAX_LEN = 50_000


def spark_session(master="local[*]", driver_memory="2g", shuffle_partitions=None, extra=None, app="mdl-etl"):
    """Tạo SparkSession cục bộ; trên Windows tự trỏ HADOOP_HOME tới winutils trong kho."""
    hadoop = STORAGE / "hadoop"
    if os.name == "nt" and hadoop.exists():
        os.environ.setdefault("HADOOP_HOME", str(hadoop))
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + str(hadoop / "bin")
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    from pyspark.sql import SparkSession
    b = (SparkSession.builder.master(master).appName(app)
         .config("spark.driver.memory", driver_memory)
         .config("spark.ui.enabled", "false")
         .config("spark.ui.showConsoleProgress", "false")
         .config("spark.sql.session.timeZone", "UTC")
         .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
         .config("spark.sql.parquet.compression.codec", "zstd")
         .config("spark.local.dir", str(STORAGE / "spark_tmp")))
    if shuffle_partitions:
        b = b.config("spark.sql.shuffle.partitions", str(shuffle_partitions))
    for k, v in (extra or {}).items():
        b = b.config(k, str(v))
    spark = b.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def staging_schemas():
    from pyspark.sql.types import ArrayType, LongType, StringType, StructField, StructType
    S, L = StringType(), LongType()

    def st(*cols):
        return StructType([StructField(n, t, True) for n, t in cols])

    meta = [("_source", S), ("_source_version", S), ("_key", S), ("_split", S), ("_raw_uri", S), ("_raw_row", L),
            ("_extra", S)]
    tactic = st(("tactic", S), ("annotated_tactic", S), ("premises", ArrayType(S)), ("state_before", S),
                ("state_after", S))
    corrupt = [("_corrupt_record", S)]
    return {
        "numinamath": st(*meta, ("source", S), ("problem", S), ("solution", S), *corrupt),
        "proofnet": st(*meta, ("id", S), ("nl_statement", S), ("nl_proof", S), ("formal_statement", S),
                       ("src_header", S), *corrupt),
        "leandojo": st(*meta, ("file_path", S), ("full_name", S), ("start_line", L), ("end_line", L),
                       ("tactics", ArrayType(tactic)), *corrupt),
        "leandojo_premise": st(("path", S), ("full_name", S), ("code", S), ("kind", S), ("start_line", L),
                               ("end_line", L), ("_raw_uri", S), ("_raw_row", L), ("_premise_idx", L)),
        "leandojo_file": st(("path", S), ("imports", ArrayType(S)), ("_raw_uri", S), ("_raw_row", L)),
    }


def _read(spark, root, name, schema):
    path = Path(root) / name
    files = sorted(str(p) for p in path.glob("*/*.jsonl"))
    if not files:
        return None
    return (spark.read.schema(schema).option("mode", "PERMISSIVE")
            .option("columnNameOfCorruptRecord", "_corrupt_record").json(files))


def _null(t="string"):
    from pyspark.sql import functions as F
    return F.lit(None).cast(t)


def _common(df):
    from pyspark.sql import functions as F
    return df.select(
        F.substring(F.sha1(F.concat_ws("|", "_source", "_key")), 1, 20).alias("record_id"),
        F.col("_source").alias("source"), F.col("_source_version").alias("source_version"),
        F.col("_key").alias("source_record_key"), F.col("_split").alias("split"),
        F.col("_raw_uri").alias("raw_uri"), F.col("_raw_row").alias("raw_row"), F.col("_extra").alias("extra_json"),
        "*")


def map_numinamath(df):
    from pyspark.sql import functions as F
    # cột `source` gốc của NuminaMath (nguồn con) trùng tên cột chung => đổi tên trước
    return _common(df.withColumnRenamed("source", "_n_source")).select(
        "record_id", "source", "source_version", "source_record_key", "split", "raw_uri", "raw_row", "extra_json",
        "_rowid",
        F.lit("problem_solution").alias("record_type"), F.col("_n_source").alias("subset"),
        F.col("problem").alias("nl_problem"), F.col("solution").alias("nl_solution"),
        _null().alias("formal_language"), _null().alias("formal_statement"), _null().alias("formal_proof"),
        _null().alias("formal_header"), _null().alias("formal_goal"), _null().alias("lean_full_name"),
        _null().alias("lean_file_path"), _null("long").alias("lean_start_line"), _null("long").alias("lean_end_line"),
        F.array().cast("array<string>").alias("tactics"), F.array().cast("array<string>").alias("premises"),
    )


def map_proofnet(df):
    from pyspark.sql import functions as F
    return _common(df).select(
        "record_id", "source", "source_version", "source_record_key", "split", "raw_uri", "raw_row", "extra_json",
        "_rowid",
        F.lit("nl_formal_pair").alias("record_type"), F.substring_index("id", "|", 1).alias("subset"),
        F.col("nl_statement").alias("nl_problem"), F.col("nl_proof").alias("nl_solution"),
        F.lit("lean3").alias("formal_language"), F.col("formal_statement"), _null().alias("formal_proof"),
        F.col("src_header").alias("formal_header"), _null().alias("formal_goal"), _null().alias("lean_full_name"),
        _null().alias("lean_file_path"), _null("long").alias("lean_start_line"), _null("long").alias("lean_end_line"),
        F.array().cast("array<string>").alias("tactics"), F.array().cast("array<string>").alias("premises"),
    )


def map_leandojo(df, premise, files):
    from pyspark.sql import Window
    from pyspark.sql import functions as F
    # khóa trùng trong corpus: giữ bản xuất hiện đầu tiên (giống baseline dict.setdefault)
    w = Window.partitionBy("path", "full_name").orderBy("_raw_row", "_premise_idx")
    prem = (premise.withColumn("_rn", F.row_number().over(w)).where("_rn = 1")
            .select(F.col("path").alias("_p_path"), F.col("full_name").alias("_p_name"), "code"))
    fw = Window.partitionBy("path").orderBy(F.col("_raw_row").desc())  # baseline: dict ghi đè => bản cuối thắng
    fil = (files.withColumn("_rn", F.row_number().over(fw)).where("_rn = 1")
           .select(F.col("path").alias("_f_path"), "imports"))
    j = (_common(df)
         .join(prem, (F.col("file_path") == F.col("_p_path")) & (F.col("full_name") == F.col("_p_name")), "left")
         .join(fil, F.col("file_path") == F.col("_f_path"), "left"))
    parts = F.split("file_path", "/")
    has_tac = F.coalesce(F.size("tactics"), F.lit(0)) > 0
    return j.select(
        "record_id", "source", "source_version", "source_record_key", "split", "raw_uri", "raw_row", "extra_json",
        "_rowid",
        F.lit("formal_theorem").alias("record_type"),
        F.when((parts[0] == ".lake") & (F.size(parts) > 2), parts[2])
         .otherwise(F.concat_ws(".", F.slice(parts, 1, 2))).alias("subset"),
        _null().alias("nl_problem"), _null().alias("nl_solution"), F.lit("lean4").alias("formal_language"),
        F.when(F.col("code").isNull(), _null())
         .otherwise(F.regexp_replace(
             F.when(F.col("code").rlike(STMT_PATTERN), F.regexp_extract("code", STMT_PATTERN, 1))
              .otherwise(F.col("code")), r"[ \t\r\n]+$", "")).alias("formal_statement"),
        F.when(has_tac, F.array_join(F.transform("tactics", lambda t: t["tactic"]), "\n")).alias("formal_proof"),
        F.when(F.coalesce(F.size("imports"), F.lit(0)) > 0, F.array_join("imports", "\n")).alias("formal_header"),
        F.when(has_tac, F.element_at("tactics", 1)["state_before"]).alias("formal_goal"),
        F.col("full_name").alias("lean_full_name"), F.col("file_path").alias("lean_file_path"),
        F.col("start_line").alias("lean_start_line"), F.col("end_line").alias("lean_end_line"),
        F.coalesce(F.transform("tactics", lambda t: t["tactic"]), F.array().cast("array<string>")).alias("tactics"),
        F.coalesce(F.array_distinct(F.flatten(F.transform("tactics", lambda t: t["premises"]))),
                   F.array().cast("array<string>")).alias("premises"),
    )


def _derive(df, manifest_df, run_id):
    from pyspark.sql import functions as F
    nl_p, nl_s = F.coalesce("nl_problem", F.lit("")), F.coalesce("nl_solution", F.lit(""))
    texts = ["nl_problem", "nl_solution", "formal_statement", "formal_proof", "formal_goal"]
    all_text = F.concat_ws("\u0001", *texts)  # \u0001 cũng là ký tự điều khiển => chỉ dùng cho W03
    lic = F.create_map(*[x for k, v in SOURCES.items() for x in (F.lit(k), F.lit(v["license"]))])
    url = F.create_map(*[x for k, v in SOURCES.items() for x in (F.lit(k), F.lit(v["url"]))])
    df = (df.withColumn("num_tactics", F.size("tactics"))
          .withColumn("latex_count", (F.regexp_count(nl_p, F.lit(LATEX_JAVA)) +
                                      F.regexp_count(nl_s, F.lit(LATEX_JAVA))).cast("long"))
          .withColumn("has_text", (F.length(nl_p) > 0) | (F.length(nl_s) > 0))
          .withColumn("has_latex", F.col("latex_count") > 0)
          .withColumn("has_lean", F.col("formal_statement").isNotNull())
          .withColumn("content_sha256", F.sha2(F.concat_ws(
              "\u001f", *[F.coalesce(c, F.lit("")) for c in
                          ("nl_problem", "nl_solution", "formal_statement", "formal_proof")]), 256)))
    ctrl = F.lit(False)
    for t in texts:
        ctrl = ctrl | F.coalesce(F.col(t).rlike(CTRL_JAVA), F.lit(False))
    odd = F.lit(False)
    for t in ("nl_problem", "nl_solution"):
        odd = odd | (F.coalesce(F.regexp_count(F.col(t), F.lit(DOLLAR_JAVA)), F.lit(0)) % 2 == 1)
    flags = F.array(
        F.when((F.col("record_type") == "nl_formal_pair") & (F.length(nl_s) == 0), F.lit("W01_EMPTY_NL_SOLUTION")),
        F.when((F.col("record_type") == "formal_theorem") & F.col("formal_statement").isNull(),
               F.lit("W02_FORMAL_STATEMENT_MISSING")),
        F.when(F.instr(all_text, "�") > 0, F.lit("W03_REPLACEMENT_CHAR")),
        F.when(ctrl, F.lit("W04_CONTROL_CHAR")),
        F.when(odd, F.lit("W05_UNBALANCED_DOLLAR")),
        F.when(F.greatest(*[F.coalesce(F.length(t), F.lit(0)) for t in texts]) > MAX_LEN, F.lit("W06_VERY_LONG")),
    )
    df = df.withColumn("quality_flags", F.filter(flags, lambda x: x.isNotNull()))
    df = (df.join(F.broadcast(manifest_df), "raw_uri", "left")
          .withColumn("license", lic[F.col("source")]).withColumn("source_url", url[F.col("source")])
          .withColumn("ingest_run_id", F.lit(run_id))
          .withColumn("pipeline_version", F.lit(PIPELINE_VERSION))
          .withColumn("schema_version", F.lit(SCHEMA_VERSION)))
    return df


def _errors():
    from pyspark.sql import functions as F
    missing = F.filter(F.array(*[F.when(F.col(c).isNull(), F.lit(c)) for c in REQUIRED]), lambda x: x.isNotNull())
    e01 = F.when(F.size(missing) > 0, F.concat(F.lit("E01_MISSING_REQUIRED:"), F.array_join(missing, ",")))
    bad = []
    for k, allowed in ENUMS.items():
        vals = [v for v in allowed if v is not None]
        ok = F.col(k).isin(vals)
        if None in allowed:
            ok = ok | F.col(k).isNull()
        bad.append(F.when(~F.coalesce(ok, F.lit(False)), F.lit(f"E02_BAD_ENUM:{k}")))
    t = F.col("record_type")
    nonempty = lambda c: F.coalesce(F.length(c), F.lit(0)) > 0  # noqa: E731
    e03 = F.when(
        ((t == "problem_solution") & ~(nonempty("nl_problem") & nonempty("nl_solution")))
        | ((t == "nl_formal_pair") & ~(nonempty("nl_problem") & nonempty("formal_statement")))
        | ((t == "formal_theorem") & ~nonempty("lean_full_name")), F.lit("E03_EMPTY_CONTENT"))
    return F.filter(F.array(e01, *bad, e03), lambda x: x.isNotNull())


def build_curated(spark, staging_root, manifest_entries, run_id, check_duplicates=True):
    """Trả về (DataFrame hợp lệ, DataFrame lỗi, DataFrame dòng hỏng)."""
    from pyspark.sql import functions as F
    sch = staging_schemas()
    parts, corrupt = [], []
    for name, mapper in (("numinamath", map_numinamath), ("proofnet", map_proofnet)):
        d = _read(spark, staging_root, name, sch[name])
        if d is not None:
            # _rowid theo thứ tự tệp/dòng: phá hòa khi hai dòng trùng hệt nhau (giống baseline giữ dòng đầu)
            d = d.withColumn("_rowid", F.monotonically_increasing_id())
            corrupt.append(d.where(F.col("_corrupt_record").isNotNull()).select(F.lit(name).alias("source"),
                                                                             "_raw_uri", "_corrupt_record"))
            parts.append(mapper(d.where(F.col("_corrupt_record").isNull())))
    d = _read(spark, staging_root, "leandojo", sch["leandojo"])
    if d is not None:
        d = d.withColumn("_rowid", F.monotonically_increasing_id())
        corrupt.append(d.where(F.col("_corrupt_record").isNotNull()).select(F.lit("leandojo").alias("source"),
                                                                         "_raw_uri", "_corrupt_record"))
        prem = _read(spark, staging_root, "leandojo_premise", sch["leandojo_premise"])
        fil = _read(spark, staging_root, "leandojo_file", sch["leandojo_file"])
        parts.append(map_leandojo(d.where(F.col("_corrupt_record").isNull()), prem, fil))
    df = parts[0]
    for p in parts[1:]:
        df = df.unionByName(p)
    rows = [(e["raw_uri"], e["sha256"], e["downloaded_at"]) for e in manifest_entries.values()]
    manifest_df = spark.createDataFrame(rows, "raw_uri string, raw_sha256 string, downloaded_at string")
    df = _derive(df, manifest_df, run_id).withColumn("_errors", _errors())
    if check_duplicates:
        # chỉ xáo trộn cột khóa (nhỏ) để tìm khóa trùng, rồi broadcast lại => tránh shuffle toàn bộ nội dung
        keys = df.select("record_id", "source_version", "raw_uri", "raw_row", "_rowid")
        dup = (keys.groupBy("record_id", "source_version")
               .agg(F.count("*").alias("_n"), F.min(F.struct("raw_uri", "raw_row", "_rowid")).alias("_first"))
               .where("_n > 1").select("record_id", "source_version", "_first"))
        df = (df.join(F.broadcast(dup), ["record_id", "source_version"], "left")
              .withColumn("_errors", F.when(
                  F.col("_first").isNotNull() & (F.struct("raw_uri", "raw_row", "_rowid") != F.col("_first")),
                  F.array_union(F.col("_errors"), F.array(F.lit("E06_DUPLICATE_KEY")))).otherwise(F.col("_errors")))
              .drop("_first"))
    good = df.where(F.size("_errors") == 0).select(*FIELD_NAMES)
    bad = df.where(F.size("_errors") > 0).select("record_id", "source", "raw_uri", "raw_row",
                                                  F.col("_errors").alias("errors"))
    bad_lines = corrupt[0]
    for c in corrupt[1:]:
        bad_lines = bad_lines.unionByName(c)
    return good, bad, bad_lines


def run_spark_etl(spark, staging_root, out_dir, manifest_entries, run_id, repartition=None,
                  max_records_per_file=None, partition_cols=tuple(PARTITION_COLS), check_duplicates=True):
    """Chạy ETL và ghi kết quả; trả metric (đếm lại từ Parquet đã ghi để không tính toán hai lần)."""
    from pyspark.sql import functions as F
    out_dir = Path(out_dir)
    t0 = time.perf_counter()
    good, bad, bad_lines = build_curated(spark, staging_root, manifest_entries, run_id, check_duplicates)
    if repartition:
        good = good.repartition(repartition, *partition_cols) if partition_cols else good.repartition(repartition)
    w = good.write.mode("overwrite")
    if max_records_per_file:
        w = w.option("maxRecordsPerFile", max_records_per_file)
    if partition_cols:
        w = w.partitionBy(*partition_cols)
    w.parquet(str(out_dir / "math_record"))
    bad.write.mode("overwrite").json(str(out_dir / "errors"))
    bad_lines.write.mode("overwrite").json(str(out_dir / "read_errors"))
    t_write = time.perf_counter() - t0
    cur = spark.read.parquet(str(out_dir / "math_record"))
    per_source = {r["source"]: r["n"] for r in cur.groupBy("source").agg(F.count("*").alias("n")).collect()}
    n_out = sum(per_source.values())
    n_err = spark.read.json(str(out_dir / "errors")).count() if any((out_dir / "errors").glob("*.json")) else 0
    n_read = spark.read.json(str(out_dir / "read_errors")).count() \
        if any(p.stat().st_size for p in (out_dir / "read_errors").glob("*.json")) else 0
    flags = {r["f"]: r["n"] for r in cur.select(F.explode("quality_flags").alias("f")).groupBy("f")
             .agg(F.count("*").alias("n")).collect()}
    files = list((out_dir / "math_record").rglob("*.parquet"))
    n_in = n_out + n_err
    return {
        "status": "ok",
        "records_in": n_in,
        "records_out": n_out,
        "records_error": n_err,
        "read_errors": n_read,
        "schema_error_rate": round((n_err + n_read) / max(1, n_in + n_read), 6),
        "per_source": per_source,
        "quality_flags": flags,
        "elapsed_s": round(t_write, 3),
        "stats_s": round(time.perf_counter() - t0 - t_write, 3),
        "throughput_rps": round(n_in / t_write, 1),
        "bytes_out": sum(p.stat().st_size for p in files),
        "files_out": len(files),
    }
