"""Tạo các mức quy mô 10K/100K/500K từ staging đầy đủ. Chạy: python scripts/tao_scales.py"""
import json

import _path  # noqa: F401
from mdl.config import STAGING, STORAGE
from mdl.scales import build_scales

res = build_scales(STAGING, STORAGE / "staging_scales")
json.dump(res, open("configs/scales.json", "w"), indent=2)
print(res)
