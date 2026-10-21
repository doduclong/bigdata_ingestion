"""Cấu hình chung: đường dẫn kho và danh mục nguồn có phiên bản cố định."""
import os
from pathlib import Path

SCHEMA_VERSION = "1.0"
PIPELINE_VERSION = "1.0.0"



def _find_storage():
    """MDL_STORAGE nếu đặt; nếu không, thư mục `_storage` gần nhất khi đi ngược lên từ mã nguồn;
    nếu không có, tạo `_storage` ngay trong thư mục dự án."""
    if os.environ.get("MDL_STORAGE"):
        return Path(os.environ["MDL_STORAGE"])
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "_storage").is_dir():
            return parent / "_storage"
    return here.parents[2] / "_storage"


# Kho dữ liệu lớn nằm ngoài mã nguồn và ngoài Git (đổi bằng biến môi trường MDL_STORAGE)
STORAGE = _find_storage()
RAW = STORAGE / "raw"
STAGING = STORAGE / "staging"

SOURCES = {
    "numinamath": {
        "version": "hf-9d8d210c",
        "license": "Apache-2.0",
        "url": "https://huggingface.co/datasets/AI-MO/NuminaMath-CoT",
        "base": "https://huggingface.co/datasets/AI-MO/NuminaMath-CoT/resolve/"
                "9d8d210c9f6a36c8f3cd84045668c9b7800ef517/data/",
        "files": ["test-00000-of-00001.parquet"] + [f"train-0000{i}-of-00005.parquet" for i in range(5)],
    },
    "proofnet": {
        "version": "git-509ad797",
        "license": "MIT",
        "url": "https://github.com/zhangir-azerbayev/ProofNet",
        "base": "https://raw.githubusercontent.com/zhangir-azerbayev/ProofNet/"
                "509ad79710ed4f46ff5c282ed5640c1aa9ac3f30/",
        "files": ["benchmark/valid.jsonl", "benchmark/test.jsonl", "LICENSE"],
    },
    "leandojo": {
        "version": "v10-29dcec07",
        "license": "CC-BY-2.0",
        "url": "https://zenodo.org/records/12740403",
        "base": "https://zenodo.org/api/records/12740403/files/",
        "files": ["leandojo_benchmark_4.tar.gz"],
    },
}

RECORD_TYPES = {
    "numinamath": "problem_solution",
    "proofnet": "nl_formal_pair",
    "leandojo": "formal_theorem",
}


def raw_dir(source, root=None):
    return Path(root or RAW) / source
