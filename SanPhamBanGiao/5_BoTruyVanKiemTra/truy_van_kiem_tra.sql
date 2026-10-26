-- Bộ truy vấn kiểm tra kho math_record (DuckDB). {t} = nguồn dữ liệu, {ids} = danh sách record_id.
-- Chạy tự động và so với kết quả mong đợi: python chay_truy_van.py [--kho <thư mục math_record>]

-- Q0_full_scan: Quét toàn bộ: đếm + tổng độ dài 2 cột văn bản lớn (đo chi phí đọc)
SELECT count(*), sum(length(coalesce(nl_solution, ''))), sum(length(coalesce(formal_statement, ''))) FROM {t};

-- Q1_count_by_source_split: Đếm theo nguồn và split (kiểm đủ bản ghi)
SELECT source, split, count(*) FROM {t} GROUP BY 1, 2 ORDER BY 1, 2;

-- Q2_olympiad_latex: Lọc NuminaMath/olympiads có LaTeX (tỉa partition + lọc cột)
SELECT count(*), round(avg(length(nl_problem)), 2) FROM {t} WHERE source = 'numinamath' AND subset = 'olympiads' AND has_latex;

-- Q3_point_lookup: Tra cứu 20 record_id (18 có, 2 không tồn tại)
SELECT record_id, source, content_sha256 FROM {t} WHERE record_id IN ({ids}) ORDER BY 1;

-- Q4_top_premises: Top-10 premise LeanDojo (unnest list)
SELECT p, count(*) AS c FROM (SELECT unnest(premises) AS p FROM {t} WHERE source = 'leandojo') GROUP BY p ORDER BY c DESC, p LIMIT 10;

-- Q5_provenance_audit: Kiểm provenance: 9 cột khác null theo nguồn/giấy phép
SELECT source, license, (source IS NOT NULL AND source_version IS NOT NULL AND raw_uri IS NOT NULL AND raw_row IS NOT NULL AND raw_sha256 IS NOT NULL AND license IS NOT NULL AND source_url IS NOT NULL AND downloaded_at IS NOT NULL AND ingest_run_id IS NOT NULL) AS ok, count(*) FROM {t} GROUP BY ALL ORDER BY 1, 2, 3;

-- ===== Truy vấn ví dụ cho các nhóm khác (math_record = view trên kho) =====
-- Đếm bản ghi theo nguồn và split
SELECT source, split, count(*) FROM math_record GROUP BY ALL ORDER BY ALL;

-- Cặp NL–Lean 3 của ProofNet theo sách
SELECT subset, count(*) FROM math_record WHERE source = 'proofnet' GROUP BY 1 ORDER BY 2 DESC;

-- Định lý Lean 4 dùng một premise cho trước
SELECT lean_full_name, formal_statement FROM math_record WHERE source = 'leandojo' AND list_contains(premises, 'Nat.succ_le_iff');

-- Truy ngược nguồn gốc một bản ghi
SELECT raw_uri, raw_row, raw_sha256, license, downloaded_at, ingest_run_id FROM math_record WHERE record_id = '<id>';

-- Bài olympiad có LaTeX cho Nhóm 8
SELECT record_id, nl_problem FROM math_record WHERE source = 'numinamath' AND subset = 'olympiads' AND has_latex LIMIT 10;
