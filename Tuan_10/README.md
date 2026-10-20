# Tuần 10 — API dữ liệu, demo, bàn giao cuối

**Nhiệm vụ:** Tích hợp API dữ liệu cho nhóm khác; demo và bảo vệ cá nhân.
**Minh chứng:** Bản bàn giao cuối; video/demo; bảng đóng góp cá nhân.

| Minh chứng | Tệp |
|---|---|
| Báo cáo tuần | `BaoCao_Tuan10.md` / `.docx` |
| Bản bàn giao cuối 1.0.0 | `math_data_lake/` (README, CHANGELOG) |
| API + client + tài liệu | `math_data_lake/src/mdl/api.py`, `client.py`, `docs/api.md` |
| Load test API | `math_data_lake/scripts/load_test_api.py`, `results/raw/tuan_10/runs_api_load.jsonl`, `results/tables/t_api_load.csv` |
| Demo | `math_data_lake/scripts/demo.py`, `docs/kich_ban_demo.md`, đầu ra `demo_output.txt` |
| Slide bảo vệ | `math_data_lake/slides/BaoVe_Nhom1.pptx` (script tạo: `slides/build_deck.js`) |
| Báo cáo cuối | `math_data_lake/report/BaoCao_BTL_Nhom1.{docx,pdf}` |
| Đóng góp + câu hỏi bảo vệ | `math_data_lake/contributions.md`, `docs/bo_cau_hoi_bao_ve.md` |

## Chạy nhanh

```
cd Tuan_10/math_data_lake
../../.venv/Scripts/python -m pytest -q tests          # 25 test
../../.venv/Scripts/python scripts/demo.py             # demo ~30 s trên mẫu
../../.venv/Scripts/python scripts/mdl.py serve        # API: http://127.0.0.1:8000/docs (cần kho đầy đủ: mdl.py etl)
```
