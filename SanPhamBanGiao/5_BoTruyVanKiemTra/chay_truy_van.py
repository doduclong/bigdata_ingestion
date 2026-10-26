"""Chạy bộ truy vấn kiểm tra Q0–Q5 trên một kho Parquet và so với kết quả mong đợi đã lưu.

Chạy:  python chay_truy_van.py                         # kho mẫu ../1_KhoParquetMau_Manifest/kho_mau
       python chay_truy_van.py --kho <.../lake/math_record> --mong-doi ket_qua_mong_doi_full.json
       python chay_truy_van.py --ghi                    # ghi lại kết quả làm mốc (chỉ khi đã kiểm chứng)
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "3_Pipeline_Ingest_ETL" / "src"))
from mdl.sql_queries import parquet_source, run_sql_queries  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--kho", default=str(HERE.parent / "1_KhoParquetMau_Manifest" / "kho_mau" / "math_record"))
ap.add_argument("--mong-doi", default=str(HERE / "ket_qua_mong_doi_mau.json"))
ap.add_argument("--ghi", action="store_true")
a = ap.parse_args()
ids = json.load(open(HERE / "query_ids.json"))["ids"]
res = run_sql_queries(parquet_source(Path(a.kho).as_posix()), ids, threads=4)
got = {k: json.loads(json.dumps(v["result"], default=str)) for k, v in res.items()}
if a.ghi:
    Path(a.mong_doi).write_text(json.dumps(got, ensure_ascii=False, indent=1), encoding="utf-8")
    print("đã ghi", a.mong_doi)
    sys.exit(0)
exp = json.loads(Path(a.mong_doi).read_text(encoding="utf-8"))
ok = True
for k, v in res.items():
    same = got[k] == exp.get(k)
    ok &= same
    print(f"{k:28s} {v['seconds']:8.4f} s  {v['rows']:3d} dòng  {'KHỚP' if same else 'KHÁC mong đợi'}")
print("TẤT CẢ KHỚP" if ok else "CÓ TRUY VẤN KHÁC KẾT QUẢ MONG ĐỢI")
sys.exit(0 if ok else 1)
