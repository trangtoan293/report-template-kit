// Bộ helper dựng template Word cho Report Builder (Superset add-on, values-report-builder.yaml).
// Cú pháp biến: {#ten_bien#}, ánh xạ theo tên cột dataset. 1 dòng dataset = 1 file in.
// Báo cáo danh sách: multi_row -> repeatRow() (engine lặp dòng thật, khuyến nghị);
// per_row -> listRow() (biến nhiều dòng nối "\n", cách cũ khi chưa có rt_multi.py).
// Dùng: const K = require('./docx_kit');  (NODE_PATH phải chứa node_modules/docx)
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, PageOrientation, Header, PageNumber, VerticalAlign, ImageRun, ShadingType, TableLayoutType,
} = require('docx');

const FONT = 'Times New Roman';
const SZ = 20; // 10pt
const SZ_LIST = 15; // 7.5pt cho các dòng chi tiết nhiều dòng
const MARGIN = 720; // 0.5"
const PORTRAIT_W = 11906 - 2 * MARGIN; // 10466 twip = bề rộng vùng in A4 dọc
const LANDSCAPE_W = 16838 - 2 * MARGIN; // 15398 twip = bề rộng vùng in A4 ngang

const LINE = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const ALL = { top: LINE, bottom: LINE, left: LINE, right: LINE };
const NO_BORDERS = { top: NONE, bottom: NONE, left: NONE, right: NONE };
const L = AlignmentType.LEFT, C = AlignmentType.CENTER, R = AlignmentType.RIGHT;

// Token luôn sinh trong 1 TextRun -> không bị Word cắt vụn thành "{#ten bien#}"
const T = (name) => `{#${name}#}`;
// Mã dòng chỉ tiêu cố định: code('b02', 0) -> 'b02_r01'
const code = (prefix, i) => `${prefix}_r${String(i + 1).padStart(2, '0')}`;

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || SZ, bold: o.bold, italics: o.italic });
const para = (text, o = {}) => new Paragraph({
  alignment: o.align || L,
  indent: o.indent ? { left: o.indent } : undefined,
  spacing: { before: o.before || 0, after: o.after || 0 },
  keepNext: o.keepNext,
  children: Array.isArray(text) ? text : [run(text, o)],
});
const label = (k, v, o = {}) => para([run(k, { bold: true }), run(v)], o);

function cell(text, w, o = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    columnSpan: o.span,
    rowSpan: o.rowSpan,
    borders: o.borders || ALL,
    verticalAlign: o.vAlign || VerticalAlign.CENTER,
    shading: o.shade ? { fill: o.shade, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 30, bottom: 30, left: 60, right: 60 },
    children: [para(text, o)],
  });
}

const table = (widths, rows, borders) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: widths,
  layout: TableLayoutType.FIXED,
  borders,
  rows,
});
const hdr = (cells) => new TableRow({ tableHeader: true, cantSplit: true, children: cells });
const row = (cells) => new TableRow({ cantSplit: true, children: cells });
// Dòng chi tiết nhiều dòng: được phép ngắt qua trang, tiêu đề bảng tự lặp lại
const listRow = (cols, widths) => new TableRow({
  cantSplit: false,
  children: cols.map(([name, align], i) => cell(T(name), widths[i], { align, size: SZ_LIST, vAlign: VerticalAlign.TOP })),
});
// Dòng lặp cho chế độ multi_row (rt_multi.py): 1 token 1 dòng/ô, engine clone dòng này cho mỗi dòng dữ liệu.
// Không dùng rowSpan(vMerge)/tableHeader/ảnh/bảng lồng trong dòng này - engine sẽ từ chối.
const repeatRow = (cols, widths) => new TableRow({
  cantSplit: true,
  children: cols.map(([name, align], i) => cell(T(name), widths[i], { align, size: SZ_LIST })),
});
const H = (t, w, o = {}) => cell(t, w, { bold: true, align: C, shade: 'F2F2F2', ...o });

// Đầu trang lặp lại mỗi trang: [trái | giữa: tiêu đề | phải: biểu mẫu + số trang]
function pageHeader(width, { left = [], title, sub = [], right = [], logo }) {
  const wSide = Math.round(width * 0.25);
  const wMid = width - 2 * wSide;
  const leftChildren = [
    ...(logo ? [new Paragraph({ children: [new ImageRun({ type: 'png', data: logo, transformation: { width: 120, height: 57 } })] })] : []),
    ...left.map((t) => para(t, { size: 18 })),
  ];
  const pageNo = new Paragraph({
    alignment: R, spacing: { before: 60 },
    children: [new TextRun({ font: FONT, size: 18, children: ['Trang ', PageNumber.CURRENT, '/', PageNumber.TOTAL_PAGES] })],
  });
  const mk = (w, children) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: NO_BORDERS, children });
  return new Header({
    children: [
      table([wSide, wMid, wSide], [new TableRow({
        children: [
          mk(wSide, leftChildren.length ? leftChildren : [para('')]),
          mk(wMid, [para(title, { align: C, bold: true, size: 28 }), ...sub.map((t) => para(t, { align: C }))]),
          mk(wSide, [...right.map((t) => para(t, { align: R, size: 18 })), pageNo]),
        ],
      })], NO_BORDERS),
      para('', { after: 60 }),
    ],
  });
}

// Khối ký: dòng ngày (cột cuối) + chức danh + khoảng ký + họ tên
function signatures(width, titles, names, withDate = true) {
  const w = Math.floor(width / titles.length);
  const widths = titles.map((_, i) => (i === titles.length - 1 ? width - w * (titles.length - 1) : w));
  // keepNext trên mọi dòng (trừ dòng tên) để khối ký không bị tách sang trang sau
  const nb = (t, cw, o = {}) => cell(t, cw, { borders: NO_BORDERS, align: C, keepNext: true, ...o });
  const rows = [];
  if (withDate) {
    rows.push(new TableRow({ children: widths.map((cw, i) => nb(i === widths.length - 1 ? `Ngày ${T('ngay_ky')} tháng ${T('thang_ky')} năm ${T('nam_ky')}` : '', cw, { italic: true })) }));
  }
  rows.push(new TableRow({ cantSplit: true, children: titles.map((t, i) => nb(t, widths[i], { bold: true })) }));
  rows.push(new TableRow({ cantSplit: true, height: { value: 1100, rule: 'atLeast' }, children: widths.map((cw) => nb('', cw)) }));
  rows.push(new TableRow({ cantSplit: true, children: names.map((n, i) => nb(T(n), widths[i], { bold: true, keepNext: false })) }));
  return [para('', { before: 200, keepNext: true }), table(widths, rows, NO_BORDERS)];
}
const SIGN_STD = (w) => signatures(w, ['Lập bảng', 'Kiểm soát', 'Lãnh đạo'], ['nguoi_lap', 'nguoi_kiem_soat', 'lanh_dao']);

// Dòng chỉ tiêu cố định: H/B đậm, S thụt lề + nghiêng
function fixedRow(widths, [stt, name, kind], tags) {
  const bold = kind === 'H' || kind === 'B';
  return row([
    cell(stt, widths[0], { align: C, bold }),
    cell(name, widths[1], { bold, italic: kind === 'S', indent: kind === 'S' ? 280 : 0 }),
    ...tags.map((t, i) => cell(T(t), widths[i + 2], { align: R, bold })),
  ]);
}

// 6 cột số dư/phát sinh chuẩn kế toán: đầu kỳ, trong kỳ, cuối kỳ x Nợ/Có
const AMT6 = ['dk_no', 'dk_co', 'ps_no', 'ps_co', 'ck_no', 'ck_co'];
const noCo = (widths, offset) => hdr(AMT6.map((_, i) => H(i % 2 ? 'Có' : 'Nợ', widths[offset + i])));
const totalRow = (labelText, labelW, span, widths, offset, prefix) => row([
  cell(labelText, labelW, { span, bold: true, align: C }),
  ...AMT6.map((f, i) => cell(T(`${prefix}_${f}`), widths[offset + i], { align: R, bold: true, size: SZ_LIST })),
]);

// Ghi file .docx: 1 section, A4, header lặp mỗi trang
async function save(file, orientation, header, children) {
  const doc = new Document({
    styles: { default: { document: { run: { font: FONT, size: SZ } } } },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838, orientation: orientation === 'portrait' ? PageOrientation.PORTRAIT : PageOrientation.LANDSCAPE },
          margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN, header: 400 },
        },
      },
      headers: { default: header },
      children,
    }],
  });
  fs.writeFileSync(file, await Packer.toBuffer(doc));
  console.log('OK', file);
}

module.exports = {
  FONT, SZ, SZ_LIST, MARGIN, PORTRAIT_W, LANDSCAPE_W, ALL, NO_BORDERS, L, C, R, VerticalAlign, TableRow,
  T, code, run, para, label, cell, table, hdr, row, listRow, repeatRow, H,
  pageHeader, signatures, SIGN_STD, fixedRow, AMT6, noCo, totalRow, save,
};
