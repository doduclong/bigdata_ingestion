"""Lối tắt cho CLI: python scripts/mdl.py <lệnh> (tương đương PYTHONPATH=src python -m mdl <lệnh>)."""
import sys

import _path  # noqa: F401
from mdl.__main__ import main

sys.exit(main())
