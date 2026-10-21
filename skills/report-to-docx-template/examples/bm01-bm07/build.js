// Ví dụ: 7 template BM01..BM07 (dựng từ các PDF báo cáo mẫu) bằng docx_kit.js.
// Chạy trong thư mục chứa docx_kit.js (copy từ scripts/):  NODE_PATH=$(npm root -g) node build.js
// Đầu ra: thư mục cha (Templates/) + rows.json cho make_data.py / outputs.py.
const fs = require('fs');
const path = require('path');
const {
  PORTRAIT_W, LANDSCAPE_W, SZ_LIST, L, C, R, VerticalAlign, TableRow,
  T, code, para, label, cell, table, hdr, row, listRow, H,
  pageHeader, signatures, SIGN_STD, fixedRow, AMT6, noCo, totalRow, save: saveTo,
} = require('./docx_kit');
const { B02, B03, BANG13 } = require('./rows');

const OUT = path.join(__dirname, '..');
const save = (name, ...rest) => saveTo(path.join(OUT, name), ...rest);

// ---------- BM01. Bảng cân đối kế toán B02/TCTD (chỉ tiêu cố định) ----------
async function bm01() {
  const W = [700, 5366, 2200, 2200];
  const head = pageHeader(PORTRAIT_W, {
    left: [T('ten_ngan_hang')],
    title: 'BẢNG CÂN ĐỐI KẾ TOÁN',
    sub: [`Tháng ${T('thang_bc')}`],
    right: ['Biểu mẫu số: B02/TCTD', '(Ban hành theo Thông tư số 49/2014/TT-NHNN ngày 31/12/2014)', `Đơn vị tính: ${T('don_vi_tinh')}`],
  });
  await save('BM01_Bang_can_doi_ke_toan_B02.docx', 'portrait', head, [
    table(W, [
      hdr([H('STT', W[0]), H('Chỉ tiêu', W[1]), H('Tháng này', W[2]), H('Tháng trước', W[3])]),
      hdr([H('', W[0]), H('1', W[1]), H('2', W[2]), H('3', W[3])]),
      ...B02.map((r, i) => fixedRow(W, r, [`${code('b02', i)}_tn`, `${code('b02', i)}_tt`])),
    ]),
    ...SIGN_STD(PORTRAIT_W),
  ]);
}

// ---------- BM02. Báo cáo kết quả hoạt động B03/TCTD ----------
async function bm02() {
  const W = [700, 4466, 1767, 1767, 1766];
  const head = pageHeader(PORTRAIT_W, {
    left: [T('ten_ngan_hang')],
    title: 'BÁO CÁO KẾT QUẢ HOẠT ĐỘNG',
    sub: [`Tháng ${T('thang_bc')}`],
    right: ['Biểu mẫu số: B03/TCTD', '(Ban hành theo Thông tư số 27/2021/TT-NHNN ngày 31/12/2021)', `Đơn vị tính: ${T('don_vi_tinh')}`],
  });
  await save('BM02_Bao_cao_ket_qua_hoat_dong_B03.docx', 'portrait', head, [
    table(W, [
      hdr([H('STT', W[0]), H('Chỉ tiêu', W[1]), H('Tháng này', W[2]), H('Tháng trước', W[3]), H('Lũy kế năm nay', W[4])]),
      ...B03.map((r, i) => fixedRow(W, r, ['tn', 'tt', 'lk'].map((s) => `${code('b03', i)}_${s}`))),
    ]),
    ...SIGN_STD(PORTRAIT_W),
  ]);
}

// ---------- BM03. Bảng 13 - Phân tích kết quả kinh doanh ----------
async function bm03() {
  const W = [700, 6766, 3000];
  const head = pageHeader(PORTRAIT_W, {
    left: [T('ten_ngan_hang')],
    title: 'PHÂN TÍCH KẾT QUẢ KINH DOANH',
    sub: [`Từ ngày ${T('tu_ngay')} đến ngày ${T('den_ngay')}`],
    right: ['Bảng 13', `Đơn vị tính: ${T('don_vi_tinh')}`],
  });
  await save('BM03_Phan_tich_ket_qua_kinh_doanh_Bang13.docx', 'portrait', head, [
    table(W, [
      hdr([H('STT', W[0]), H('Chỉ tiêu', W[1]), H('Tăng/Giảm', W[2])]),
      ...BANG13.map((r, i) => fixedRow(W, r, [code('b13', i)])),
    ]),
    ...SIGN_STD(PORTRAIT_W),
  ]);
}

// ---------- BM04. Bảng cân đối tài khoản cấp III (danh sách, 2 phần A/B) ----------
function cdtkSection(W, title, p) {
  return [
    para(title, { bold: true, size: 22, before: 120, after: 60, keepNext: true }),
    table(W, [
      hdr([H('Tên tài khoản', W[0], { rowSpan: 2 }), H('TK NHNN', W[1], { rowSpan: 2 }), H('TK FCC', W[2], { rowSpan: 2 }),
        H('Số dư đầu kỳ', W[3] + W[4], { span: 2 }), H('Doanh số trong kỳ', W[5] + W[6], { span: 2 }), H('Số dư cuối kỳ', W[7] + W[8], { span: 2 })]),
      noCo(W, 3),
      listRow([[`${p}_ten_tk`, L], [`${p}_tk_nhnn`, C], [`${p}_tk_fcc`, C], ...AMT6.map((f) => [`${p}_${f}`, R])], W),
      totalRow('Tổng cộng:', W[0] + W[1] + W[2], 3, W, 3, `tong_${p}`),
    ]),
  ];
}
async function bm04() {
  const W = [3550, 950, 1000, 1650, 1650, 1650, 1650, 1650, 1648];
  const head = pageHeader(LANDSCAPE_W, {
    left: [T('ten_ngan_hang'), `Đơn vị: ${T('ten_don_vi')}`],
    title: 'BẢNG CÂN ĐỐI TÀI KHOẢN CẤP III',
    sub: [`Loại nguyên tệ: ${T('loai_nguyen_te')}`, `Từ ngày ${T('tu_ngay')} đến ngày ${T('den_ngay')}`],
    right: [`Biểu mẫu số: ${T('bieu_mau')}`, T('can_cu_ban_hanh'), `Đơn vị tính: ${T('don_vi_tinh')}`],
  });
  await save('BM04_Bang_can_doi_tai_khoan_cap_III.docx', 'landscape', head, [
    ...cdtkSection(W, 'A. Các tài khoản trong bảng cân đối kế toán', 'a'),
    ...cdtkSection(W, 'B. Các tài khoản ngoài bảng cân đối kế toán', 'b'),
    ...SIGN_STD(LANDSCAPE_W),
  ]);
}

// ---------- BM05. Bảng cân đối kế toán TK cấp 4 (theo chi nhánh / loại tiền) ----------
async function bm05() {
  const W = [3400, 2000, 2000, 2000, 2000, 2000, 1998];
  const head = pageHeader(LANDSCAPE_W, {
    left: [T('ten_ngan_hang')],
    title: 'BẢNG CÂN ĐỐI KẾ TOÁN (TK CẤP 4)',
    sub: [`Từ ngày ${T('tu_ngay')} đến ngày ${T('den_ngay')}`],
    right: [`Đơn vị tính: ${T('don_vi_tinh')}`],
  });
  await save('BM05_Bang_can_doi_ke_toan_TK_cap_4.docx', 'landscape', head, [
    label('Mã tài khoản: ', T('ma_tk')),
    label('Tên tài khoản: ', T('ten_tk'), { after: 120 }),
    table(W, [
      hdr([H('Chi nhánh / Loại tiền', W[0], { rowSpan: 2 }), H('Số dư đầu kỳ', W[1] + W[2], { span: 2 }),
        H('Phát sinh trong kỳ', W[3] + W[4], { span: 2 }), H('Số dư cuối kỳ', W[5] + W[6], { span: 2 })]),
      noCo(W, 1),
      listRow([['ct_loai_tien', L], ...AMT6.map((f) => [`ct_${f}`, R])], W),
      new TableRow({ cantSplit: true, children: [
        cell(T('tc_loai_tien'), W[0], { bold: true, size: SZ_LIST, vAlign: VerticalAlign.TOP }),
        ...AMT6.map((f, i) => cell(T(`tc_${f}`), W[1 + i], { align: R, bold: true, size: SZ_LIST, vAlign: VerticalAlign.TOP })),
      ] }),
    ]),
    ...SIGN_STD(LANDSCAPE_W),
  ]);
}

// ---------- BM06. Nhật ký sổ cái (TK cấp 3) - BM-KT-046 ----------
async function bm06() {
  const W = [1300, 4100, 1666, 1666, 1666, 1666, 1666, 1668];
  const head = pageHeader(LANDSCAPE_W, {
    left: [T('ten_ngan_hang')],
    title: 'NHẬT KÝ SỔ CÁI (TK CẤP 3)',
    sub: [`Từ ngày ${T('tu_ngay')} đến ngày ${T('den_ngay')}`],
    right: ['Biểu mẫu số: BM-KT-046', `Đơn vị tính: ${T('don_vi_tinh')}`],
  });
  await save('BM06_Nhat_ky_so_cai_TK_cap_3.docx', 'landscape', head, [
    label('Số tài khoản: ', T('so_tk')),
    label('Tên tài khoản: ', T('ten_tk'), { after: 120 }),
    table(W, [
      hdr([H('Số tài khoản', W[0], { rowSpan: 2 }), H('Tên tài khoản', W[1], { rowSpan: 2 }), H('Dư đầu', W[2] + W[3], { span: 2 }),
        H('Phát sinh', W[4] + W[5], { span: 2 }), H('Dư cuối', W[6] + W[7], { span: 2 })]),
      noCo(W, 2),
      listRow([['ct_so_tk', L], ['ct_ten_tk', L], ...AMT6.map((f) => [`ct_${f}`, R])], W),
      totalRow('Tổng cộng', W[0] + W[1], 2, W, 2, 'tong'),
    ]),
    ...SIGN_STD(LANDSCAPE_W),
  ]);
}

// ---------- BM07. Nhật ký quỹ toàn chi nhánh (1 file / 1 loại tiền) ----------
async function bm07() {
  const W = [1900, 4298, 2300, 2300, 2700, 1900];
  const head = pageHeader(LANDSCAPE_W, {
    logo: fs.readFileSync(path.join(__dirname, 'logo.png')),
    title: 'NHẬT KÝ QUỸ TOÀN CHI NHÁNH',
    sub: [`Ngày số liệu: ${T('ngay_so_lieu')}`, `Loại tiền: ${T('loai_tien')}`],
    right: [`Ngày tạo: ${T('ngay_tao')}`],
  });
  const sumRow = (text, tag, col) => row(W.map((w, i) => {
    if (i === 1) return cell(text, w, { bold: true, align: R });
    return cell(i === col ? T(tag) : '', w, { align: R, bold: true });
  }));
  await save('BM07_Nhat_ky_quy_toan_chi_nhanh.docx', 'landscape', head, [
    label('Ngân hàng: ', T('ten_ngan_hang')),
    label('Đơn vị: ', T('don_vi'), { after: 120 }),
    table(W, [
      hdr([H('Số chứng từ', W[0]), H('Diễn giải', W[1]), H('Tiền thu', W[2]), H('Tiền chi', W[3]), H('Giao dịch viên', W[4]), H('Số C.Từ theo GDV', W[5])]),
      listRow([['ct_so_ct', L], ['ct_dien_giai', L], ['ct_tien_thu', R], ['ct_tien_chi', R], ['ct_giao_dich_vien', L], ['ct_so_ct_gdv', L]], W),
      sumRow('Dư đầu kỳ:', 'du_dau_ky', 2),
      sumRow('Tổng thu:', 'tong_thu', 2),
      sumRow('Tổng chi:', 'tong_chi', 3),
      sumRow('Dư cuối kỳ:', 'du_cuoi_ky', 2),
    ]),
    ...signatures(LANDSCAPE_W, ['Thủ quỹ', 'P. Kế toán & Quỹ', 'Tổng giám đốc'], ['thu_quy', 'ke_toan_quy', 'tong_giam_doc'], false),
  ]);
}

(async () => {
  for (const f of [bm01, bm02, bm03, bm04, bm05, bm06, bm07]) await f();
  // Xuất danh mục chỉ tiêu cố định cho script sinh cấu trúc dữ liệu / dữ liệu mẫu
  fs.writeFileSync(path.join(__dirname, 'rows.json'), JSON.stringify({ B02, B03, BANG13 }, null, 1));
})().catch((e) => { console.error(e); process.exit(1); });
