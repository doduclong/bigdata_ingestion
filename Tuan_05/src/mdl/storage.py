"""Bố trí lưu trữ vùng curated: định dạng, partition, kích thước tệp; phát hiện và xử lý small-file problem."""
import math
import shutil
import time
from pathlib import Path

TARGET_MB = 128

LAYOUTS = {
    # tên: (định dạng, cột partition, maxRecordsPerFile, mô tả)
    "L0_jsonl": ("jsonl", (), None, "Baseline: một tệp JSONL không nén, không partition"),
    "L1_parquet_flat": ("parquet", (), None, "Parquet zstd, không partition, tệp ~128 MB"),
    "L2_parquet_src_ver": ("parquet", ("source", "source_version"), None,
                           "Parquet zstd, partition source/source_version, tệp ~128 MB (đề xuất)"),
    "L3_parquet_src_ver_subset": ("parquet", ("source", "source_version", "subset"), None,
                                  "Parquet zstd, partition sâu thêm theo subset (1 tệp/partition)"),
    "L4_parquet_small_files": ("parquet", ("source", "source_version"), 2000,
                               "Như L2 nhưng tối đa 2.000 bản ghi/tệp (mô phỏng nạp nhiều batch nhỏ)"),
    "L5_parquet_compacted": ("parquet", ("source", "source_version"), None, "L4 sau khi chạy compaction"),
    "L6_parquet_src_ver_rg16": ("parquet", ("source", "source_version"), None,
                                "Như L2 nhưng row group 16 MB (nhiều đơn vị đọc song song hơn trong mỗi tệp)"),
}


def dir_stats(path):
    files = [p for p in Path(path).rglob("*") if p.is_file() and p.suffix in (".parquet", ".jsonl", ".json")]
    sizes = [p.stat().st_size for p in files]
    return {"files": len(files), "bytes": sum(sizes), "partitions": len({p.parent for p in files}),
            "avg_file_mb": round(sum(sizes) / len(sizes) / 2**20, 3) if sizes else 0,
            "min_file_kb": round(min(sizes) / 1024, 1) if sizes else 0,
            "max_file_mb": round(max(sizes) / 2**20, 2) if sizes else 0,
            "small_files_lt_8mb": sum(1 for s in sizes if s < 8 * 2**20)}


def _n_files(nbytes, target_mb=TARGET_MB):
    return max(1, math.ceil(nbytes / (target_mb * 2**20)))


def write_layout(spark, df, out, layout, source_bytes, target_mb=TARGET_MB):
    """Ghi `df` (curated, có cột source/source_version) theo layout.

    source_bytes: {(source, version): bytes Parquet hiện có} — để chọn số tệp đạt kích thước mục tiêu.
    """
    from pyspark.sql import functions as F
    fmt, pcols, max_rec, _ = LAYOUTS[layout]
    out = Path(out)
    shutil.rmtree(out, ignore_errors=True)
    t0 = time.perf_counter()
    if layout == "L1_parquet_flat":
        df.repartition(_n_files(sum(source_bytes.values()), target_mb)).write.parquet(str(out))
    elif layout in ("L2_parquet_src_ver", "L6_parquet_src_ver_rg16"):
        rg = {"parquet.block.size": 16 * 2**20} if layout.endswith("rg16") else {}
        # ghi từng partition riêng với đúng số tệp mục tiêu (repartition theo cột sẽ dồn cả nguồn vào 1 tệp)
        for (src, ver), nbytes in source_bytes.items():
            part = df.where((F.col("source") == src) & (F.col("source_version") == ver)).drop(*pcols)
            part.repartition(_n_files(nbytes, target_mb)).write.options(**rg).parquet(
                str(out / f"source={src}" / f"source_version={ver}"))
    elif layout == "L3_parquet_src_ver_subset":
        n = df.select(*pcols).distinct().count()
        df.repartition(n, *pcols).write.partitionBy(*pcols).parquet(str(out))
    elif layout == "L4_parquet_small_files":
        # mỗi task chứa đủ mọi nguồn => mỗi task ghi tệp nhỏ vào mọi partition, rồi cắt tiếp theo 2.000 bản ghi
        df.repartition(16).write.option("maxRecordsPerFile", max_rec).partitionBy(*pcols).parquet(str(out))
    else:
        raise ValueError(layout)
    for junk in out.rglob("_SUCCESS"):
        junk.unlink()
    for junk in out.rglob(".*.crc"):
        junk.unlink()
    return round(time.perf_counter() - t0, 3)


def compact(spark, path, target_mb=TARGET_MB):
    """Gộp tệp nhỏ: mỗi thư mục lá được ghi lại thành ceil(bytes/target) tệp rồi hoán đổi (rename) sang chỗ cũ."""
    path = Path(path)
    t0 = time.perf_counter()
    rewritten = before = after = 0
    for d in sorted({p.parent for p in path.rglob("*.parquet")}):
        files = sorted(d.glob("*.parquet"))
        before += len(files)
        n = _n_files(sum(p.stat().st_size for p in files), target_mb)
        if len(files) <= n:
            after += len(files)
            continue
        tmp, old = d.with_name(d.name + ".compacting"), d.with_name(d.name + ".old")
        shutil.rmtree(tmp, ignore_errors=True)
        spark.read.parquet(*[str(p) for p in files]).repartition(n).write.parquet(str(tmp))
        d.rename(old)  # hoán đổi: người đọc thấy bản cũ hoặc bản mới, không thấy bản dở dang
        tmp.rename(d)
        shutil.rmtree(old)
        for junk in list(d.glob("_SUCCESS")) + list(d.glob(".*.crc")):
            junk.unlink()
        after += len(list(d.glob("*.parquet")))
        rewritten += 1
    return {"compaction_s": round(time.perf_counter() - t0, 3), "partitions_rewritten": rewritten,
            "files_before": before, "files_after": after}
