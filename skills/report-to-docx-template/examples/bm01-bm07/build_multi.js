// Ví dụ chế độ multi_row: BM04M - Bảng cân đối TK cấp III dùng DÒNG LẶP THẬT (rt_multi.py).
// Dataset dạng "dài": 1 dòng = 1 tài khoản; group_by = khoá báo cáo; dòng lặp lọc theo cột `phan`.
// Report Builder: Report mode = Multiple rows; Group by: ma_don_vi, tu_ngay, den_ngay, loai_nguyen_te;
//   Repeat rows: t1r3 (phan = A), t2r3 (phan = B); Sort: sort_key.
// Chạy: NODE_PATH=$(npm root -g) node build_multi.js
const path = require('path');
const {
  LANDSCAPE_W, L, C, R, T, para, table, hdr, repeatRow, H, pageHeader, SIGN_STD, AMT6, noCo, totalRow, save,
} = require('./docx_kit');

const W = [3550, 950, 1000, 1650, 1650, 1650, 1650, 1650, 1648];

// Mỗi phần là 1 bảng riêng: r1-r2 tiêu đề, r3 dòng lặp, r4 tổng cộng
const section = (title, p) => [
  para(title, { bold: true, size: 22, before: 120, after: 60, keepNext: true }),
  table(W, [
    hdr([H('Tên tài khoản', W[0], { rowSpan: 2 }), H('TK NHNN', W[1], { rowSpan: 2 }), H('TK FCC', W[2], { rowSpan: 2 }),
      H('Số dư đầu kỳ', W[3] + W[4], { span: 2 }), H('Doanh số trong kỳ', W[5] + W[6], { span: 2 }), H('Số dư cuối kỳ', W[7] + W[8], { span: 2 })]),
    noCo(W, 3),
    repeatRow([['ten_tk', L], ['tk_nhnn', C], ['tk_fcc', C], ...AMT6.map((f) => [f, R])], W),
    totalRow('Tổng cộng:', W[0] + W[1] + W[2], 3, W, 3, `tong_${p}`),
  ]),
];

(async () => {
  const head = pageHeader(LANDSCAPE_W, {
    left: [T('ten_ngan_hang'), `Đơn vị: ${T('ten_don_vi')}`],
    title: 'BẢNG CÂN ĐỐI TÀI KHOẢN CẤP III',
    sub: [`Loại nguyên tệ: ${T('loai_nguyen_te')}`, `Từ ngày ${T('tu_ngay')} đến ngày ${T('den_ngay')}`],
    right: [`Biểu mẫu số: ${T('bieu_mau')}`, T('can_cu_ban_hanh'), `Đơn vị tính: ${T('don_vi_tinh')}`],
  });
  await save(path.join(__dirname, '..', 'BM04M_Bang_can_doi_tai_khoan_cap_III_multi.docx'), 'landscape', head, [
    ...section('A. Các tài khoản trong bảng cân đối kế toán', 'a'),
    ...section('B. Các tài khoản ngoài bảng cân đối kế toán', 'b'),
    ...SIGN_STD(LANDSCAPE_W),
  ]);
})().catch((e) => { console.error(e); process.exit(1); });
