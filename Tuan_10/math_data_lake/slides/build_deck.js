// Slide bảo vệ Nhóm 1 — Math Data Lake. Số liệu chép từ results/tables (sinh từ raw results).
// Chạy: node build_deck.js <đường_dẫn_output.pptx> <thư_mục_figures>
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const OUT = process.argv[2];
const FIG = process.argv[3];
const THEME = {
  name: "Math Data Lake",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2333", lt1: "FFFFFF", dk2: "22304A", lt2: "EEF2F7",
    accent1: "0E8C7F", accent2: "E3A33B", accent3: "5B6B8C", accent4: "C8553D",
    accent5: "7FB7BE", accent6: "A0A9B8", hlink: "0E8C7F", folHlink: "5B6B8C",
  },
};
const HEX = THEME.colors;

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33" x 7.5"
  pres.title = "Math Data Lake — Nhóm 1";
  pres.author = "Nhóm 1 INT4418";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "DARK",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 11.7, h: 1.6, fontSize: 40, bold: true,
        color: C.background1, valign: "bottom" }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.0, w: 11.7, h: 1.8, fontSize: 18,
        color: C.background2, valign: "top" }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: C.background1 },
    margin: [0.5, 0.6, 0.6, 0.6],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 32, bold: true,
        color: C.text2, valign: "middle" }, text: "" } },
      { text: { text: "Nhóm 1 · Math Data Lake · INT4418", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10,
        color: C.accent3 } } },
    ],
    slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent3 },
  });

  const card = (s, x, y, w, h, name) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: name });
  const stat = (s, x, y, w, big, label, color) => {
    s.addText(big, { x, y, w, h: 0.9, fontSize: 40, bold: true, color: color || C.accent1, fontFace: "Cambria",
      isTextBox: true, margin: 0 });
    s.addText(label, { x, y: y + 0.9, w, h: 0.7, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  };
  const chartBase = (title) => ({
    showTitle: true, title, titleFontSize: 14, titleColor: HEX.dk2, titleFontFace: "+mj-lt",
    catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent3, catAxisLabelFontFace: "+mn-lt",
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
    valGridLine: { color: "DDE3EC", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelFontSize: 11, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", showLegend: false,
  });

  // 1. Tiêu đề
  pres.addSection({ title: "Mở đầu" });
  let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Mở đầu" });
  s.addText("Math Data Lake: hợp nhất dữ liệu toán học đa biểu diễn, truy vết tới từng dòng raw", { placeholder: "title" });
  s.addText("Nhóm 1 · INT4418 Dữ liệu lớn · PTIT · GV: TS. Nguyễn Kiều Linh\nNuminaMath-CoT + ProofNet + LeanDojo Benchmark 4 · 982.477 bản ghi · bản 1.0.0",
    { placeholder: "body" });
  s.addNotes("TV1 mở đầu: một câu về mục tiêu — kho dữ liệu toán đa nguồn, có lược đồ chung, truy vấn được, truy vết được nguồn gốc. Giới thiệu nhóm 7 người và vai trò.");

  // 2. Bài toán
  pres.addSection({ title: "Bài toán" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Bài toán" });
  s.addText("Ba nguồn, ba định dạng, ba ngôn ngữ biểu diễn", { placeholder: "title" });
  const src = [
    ["NuminaMath-CoT", "859.594 bài · văn bản + LaTeX", "Parquet · không có ID gốc", C.accent1],
    ["ProofNet", "371 cặp NL – Lean 3", "JSONL · khóa Sách|bài", C.accent2],
    ["LeanDojo Benchmark 4", "122.517 định lý Lean 4", "mảng JSON 373 MB + corpus", C.accent4],
  ];
  src.forEach(([t, a, b, col], i) => {
    const x = 0.6 + i * 4.15;
    card(s, x, 1.5, 3.85, 2.2, `nguon-${i}`);
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 1.75, w: 0.5, h: 0.5, fill: { color: col }, line: { color: col },
      objectName: `cham-${i}` });
    s.addText(t, { x: x + 0.95, y: 1.7, w: 2.8, h: 0.6, fontSize: 18, bold: true, color: C.text2, isTextBox: true, margin: 0 });
    s.addText([{ text: a, options: { breakLine: true } }, { text: b }], { x: x + 0.3, y: 2.45, w: 3.4, h: 1.1,
      fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top", paraSpaceAfter: 4 });
  });
  s.addText([
    { text: "RQ1 ", options: { bold: true, color: C.accent1 } },
    { text: "Hợp nhất văn bản, LaTeX, Lean vào một lược đồ mà không mất provenance?", options: { breakLine: true } },
    { text: "RQ2 ", options: { bold: true, color: C.accent1 } },
    { text: "Định dạng và chia vùng ảnh hưởng thế nào tới thời gian, RAM, dung lượng khi 10K → 982K?", options: { breakLine: true } },
    { text: "Nút thắt: ", options: { bold: true, color: C.accent4 } },
    { text: "đa dạng · mảng JSON phải nạp trọn vào RAM · chi phí đọc–ghi · số tệp nhỏ · cập nhật gia tăng" },
  ], { x: 0.6, y: 4.1, w: 12.1, h: 2.5, fontSize: 18, color: C.text1, isTextBox: true, margin: 0, valign: "top",
    paraSpaceAfter: 10 });
  s.addNotes("TV1: ba nguồn khác nhau về định dạng, khóa và biểu diễn. Hai câu hỏi nghiên cứu. Nhấn mạnh nút thắt Big Data là đa dạng + khối lượng + small files + cập nhật.");

  // 3. Kiến trúc
  pres.addSection({ title: "Hệ thống" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Hệ thống" });
  s.addText("Kiến trúc: raw → staging → Spark ETL → Parquet", { placeholder: "title" });
  s.addImage({ path: path.join(FIG, "h1_kien_truc.png"), x: 0.6, y: 1.45, w: 12.1, h: 3.17, objectName: "kien-truc" });
  s.addText([
    { text: "Lược đồ math_record 37 cột · record_id = sha1(source|key)[:20]", options: { bullet: true, breakLine: true } },
    { text: "Provenance bắt buộc: raw_uri, raw_row, raw_sha256, license, downloaded_at, ingest_run_id", options: { bullet: true, breakLine: true } },
    { text: "Parquet zstd · partition source/source_version · row group 16 MB · sắp xếp record_id · _lake_log", options: { bullet: true } },
  ], { x: 0.6, y: 4.9, w: 12.1, h: 1.8, fontSize: 16, color: C.text1, isTextBox: true, valign: "top", paraSpaceAfter: 6 });
  s.addNotes("TV5/TV6: đi qua từng vùng. Bản Python tham chiếu là đặc tả; Spark dùng cùng biểu thức chính quy nên parity 100%.");

  // 4. RQ1
  pres.addSection({ title: "Kết quả" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
  s.addText("RQ1: hợp nhất ~1 triệu bản ghi mà không mất nguồn gốc", { placeholder: "title" });
  const st1 = [["982.477", "bản ghi curated / 982.482 vào"], ["0,0005%", "tỷ lệ lỗi lược đồ (5 bản ghi)"],
    ["100%", "bản ghi có đủ 9 cột provenance"], ["30/30", "bản ghi truy vết đúng dòng raw, sha256 khớp"],
    ["0", "khác biệt Spark ↔ Python trên 36 cột"], ["122.512", "định lý join được corpus Lean (100%)"]];
  st1.forEach(([b, l], i) => {
    const x = 0.6 + (i % 3) * 4.15, y = 1.6 + Math.floor(i / 3) * 2.55;
    card(s, x, y, 3.85, 2.25, `rq1-${i}`);
    stat(s, x + 0.3, y + 0.3, 3.3, b, l, i === 1 ? C.accent4 : C.accent1);
  });
  s.addNotes("TV7: các bằng chứng cho RQ1. 5 lỗi là 'định lý' không tên trong tệp định nghĩa cú pháp của LeanDojo. Truy vết đọc lại đúng dòng raw, mảng JSON đọc theo luồng.");

  // 5. RQ2 quy mô
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
  s.addText("RQ2: Spark trên một máy chỉ thắng ở quy mô lớn", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "Runtime 982K (s)", labels: ["Python 1 nhân", "Spark 2 nhân", "Spark 4 nhân", "Spark 8 nhân"],
    values: [65.8, 75.2, 53.8, 59.8] }], { x: 0.6, y: 1.45, w: 6.6, h: 4.9, barDir: "col",
    chartColors: [HEX.accent3, HEX.accent3, HEX.accent1, HEX.accent3], ...chartBase("Runtime end-to-end ở 982K bản ghi (s, median 3 lần)"),
    dataLabelFormatCode: "0.0", valAxisLabelFormatCode: "0" });
  s.addText([
    { text: "10K: Python 1,4 s · Spark 13–25 s (chi phí cố định)", options: { bullet: true, breakLine: true } },
    { text: "Điểm hòa vốn giữa 500K và 982K", options: { bullet: true, breakLine: true } },
    { text: "8 nhân chậm hơn 4 nhân: heap 2 GB dùng chung, tràn đĩa", options: { bullet: true, breakLine: true } },
    { text: "Spark đọc 9,7 GB cho 1,8 GB đầu vào (×5)", options: { bullet: true } },
  ], { x: 7.6, y: 1.6, w: 5.1, h: 3.4, fontSize: 16, color: C.text1, isTextBox: true, valign: "top", paraSpaceAfter: 8 });
  s.addText("Giới hạn chung: ≤ 3,5 GB RAM mỗi lần chạy", { x: 7.6, y: 5.4, w: 5.1, h: 0.5, fontSize: 14, italic: true,
    color: C.accent4, isTextBox: true });
  s.addNotes("TV6: kết quả trung thực — Spark không tăng tốc tuyến tính. Baseline đơn giản rất cạnh tranh ở quy mô này.");

  // 6. Lưu trữ
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
  s.addText("Định dạng cột và kích thước tệp quyết định chi phí", { placeholder: "title" });
  const L = ["L0 JSONL", "L1 phẳng", "L2 nguồn", "L3 +subset", "L4 tệp nhỏ", "L5 gộp", "L6 RG16"];
  s.addChart(pres.charts.BAR, [{ name: "MB", labels: L, values: [2340.8, 454.3, 446.1, 424.1, 465.1, 450.9, 446.7] }],
    { x: 0.6, y: 1.45, w: 6.0, h: 4.6, barDir: "col", chartColors: [HEX.accent2], ...chartBase("Dung lượng (MB)"),
      dataLabelFormatCode: "0", valAxisLabelFormatCode: "0" });
  s.addChart(pres.charts.BAR, [{ name: "s", labels: L, values: [6.57, 0.611, 0.692, 0.736, 0.936, 0.622, 0.610] }],
    { x: 6.75, y: 1.45, w: 6.0, h: 4.6, barDir: "col", chartColors: [HEX.accent1], ...chartBase("Tổng 6 truy vấn DuckDB (s)"),
      dataLabelFormatCode: "0.00", valAxisLabelFormatCode: "0" });
  s.addText("Parquet nhỏ hơn 5,2× và nhanh hơn 10,8× · 512 tệp nhỏ: +53% thời gian truy vấn · compaction khôi phục hoàn toàn",
    { x: 0.6, y: 6.2, w: 12.1, h: 0.6, fontSize: 15, color: C.text1, isTextBox: true });
  s.addNotes("TV6: 7 cấu hình, 3 lần ghi, 3 lần truy vấn, kết quả 21/21 khớp L0. Row group 16 MB giúp lọc LeanDojo nhanh gấp 2,8 lần.");

  // 7. Gia tăng + API
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Kết quả" });
  s.addText("Nạp gia tăng và API dữ liệu cho Nhóm 2–8", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "s", labels: ["Dựng lại toàn bộ", "v1 batch 171.898", "v2 nạp lại"], values: [52.5, 22.3, 17.6] }],
    { x: 0.6, y: 1.45, w: 6.0, h: 4.4, barDir: "col", chartColors: [HEX.accent3, HEX.accent1, HEX.accent2],
      ...chartBase("Runtime nạp (s, median 3 lần)"), dataLabelFormatCode: "0.0", valAxisLabelFormatCode: "0" });
  card(s, 6.9, 1.45, 5.85, 4.4, "api-card");
  s.addText([
    { text: "API FastAPI + DuckDB", options: { bold: true, fontSize: 18, color: C.text2, breakLine: true } },
    { text: "/records, /pairs/nl-formal, /premises/{p}/theorems, /provenance, /export", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "1 client: 31,6 QPS · P95 57 ms", options: { bullet: true, breakLine: true } },
    { text: "10 client: 85 QPS · P95 169 ms", options: { bullet: true, breakLine: true } },
    { text: "50 client: 88,5 QPS · P95 773 ms (bão hòa)", options: { bullet: true, breakLine: true } },
    { text: "0 lỗi / 13.500 request · RAM ≤ 483 MB", options: { bullet: true } },
  ], { x: 7.2, y: 1.65, w: 5.3, h: 4.0, fontSize: 15, color: C.text1, isTextBox: true, valign: "top", paraSpaceAfter: 4 });
  s.addText("Kho sau gia tăng trùng khớp hoàn toàn với bản dựng lại · nạp lại: 0 bản ghi mới · nội dung đổi cùng phiên bản bị từ chối (E07)",
    { x: 0.6, y: 6.1, w: 12.1, h: 0.6, fontSize: 14, color: C.text1, isTextBox: true });
  s.addNotes("TV7/TV1: _lake_log, idempotent, minor compaction. API: client Python mdl.client, tài liệu docs/api.md.");

  // 8. Ablation
  pres.addSection({ title: "Phân tích" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Phân tích" });
  s.addText("Điểm nghẽn là CPU và việc quét lại, không phải đọc đĩa", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [
    { name: "Đọc + parse JSON", labels: ["Spark ETL 982K"], values: [2.0] },
    { name: "Ánh xạ, regex, join", labels: ["Spark ETL 982K"], values: [21.9] },
    { name: "Kiểm tra trùng khóa", labels: ["Spark ETL 982K"], values: [6.4] },
    { name: "Ghi Parquet zstd", labels: ["Spark ETL 982K"], values: [25.4] },
  ], { x: 0.6, y: 1.45, w: 12.1, h: 2.4, barDir: "bar", barGrouping: "stacked",
    chartColors: [HEX.accent3, HEX.accent2, HEX.accent4, HEX.accent1], ...chartBase("Phân rã 55,8 s (median 3 lần)"),
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", dataLabelPosition: "ctr",
    dataLabelColor: HEX.lt1, dataLabelFormatCode: "0.0", valAxisLabelFormatCode: "0" });
  const abl = [["−30%", "tắt kiểm tra trùng khóa: bỏ lần quét lại 3,7 GB"], ["×1,9", "tra cứu điểm nhanh hơn khi sắp xếp theo record_id"],
    ["×3,2", "dung lượng nếu không nén (truy vấn −30%)"], ["+9%", "chia split 32 MB: thêm task, thêm tệp"]];
  abl.forEach(([b, l], i) => {
    const x = 0.6 + i * 3.1;
    card(s, x, 4.15, 2.85, 2.5, `abl-${i}`);
    stat(s, x + 0.25, 4.35, 2.4, b, l, C.accent1);
  });
  s.addNotes("TV5: ablation 7 cấu hình × 3 lần. Kiểm tra trùng khóa đắt nhất: cải tiến là kiểm tra sau khi ghi trên cột record_id.");

  // 9. Phân tích lỗi
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Phân tích" });
  s.addText("Phân tích lỗi trên dữ liệu thật", { placeholder: "title" });
  const errs = [
    ["5", "định lý LeanDojo không tên: thực chất là định nghĩa cú pháp (proof_wanted, DeprecateMe)", C.accent4],
    ["95%", "cờ $ lẻ là ký hiệu tiền tệ (orca_math): dương tính giả", C.accent2],
    ["0x0B/0x0C", "ký tự điều khiển = ligature ff/fi font TeX OT1 sót từ PDF (aops_forum)", C.accent3],
    ["3,99% → 0,001%", "tách phát biểu Lean sai do := trong @[attr]; sửa bằng regex mức ngoặc 0", C.accent1],
  ];
  errs.forEach(([b, l, col], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.6;
    card(s, x, y, 5.9, 2.3, `loi-${i}`);
    s.addText(b, { x: x + 0.3, y: y + 0.25, w: 5.3, h: 0.8, fontSize: 32, bold: true, color: col, fontFace: "Cambria",
      isTextBox: true, margin: 0 });
    s.addText(l, { x: x + 0.3, y: y + 1.1, w: 5.3, h: 1.0, fontSize: 15, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  });
  s.addNotes("TV2/TV3/TV4: giả thuyết ban đầu về \\f bị bác bỏ khi xem ví dụ — minh họa vì sao cần error analysis trên dữ liệu thật.");

  // 10. Kết luận
  pres.addSection({ title: "Kết luận" });
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Kết luận" });
  s.addText("Bàn giao: kho, contract v1.0, API, 25 test", { placeholder: "title" });
  s.addText([
    { text: "Giới hạn: một máy, RAM ≤ 4 GB, không có ACID khi compaction, phân loại lỗi bằng quy tắc", options: { breakLine: true } },
    { text: "Tiếp theo: kiểm trùng sau khi ghi · Iceberg/Delta · snapshot nguồn mới · chạy trên cụm" },
  ], { placeholder: "body" });
  s.addNotes("TV1: tóm tắt trả lời RQ1/RQ2, sản phẩm bàn giao, giới hạn, mời câu hỏi.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
