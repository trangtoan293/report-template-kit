// Ví dụ template Dashboard Export (values-dashboard-export.yaml, dr_docx.py):
// - {#dashboard#} đúng 1 lần, đoạn riêng trong thân văn bản (không trong bảng/header/footer) -> bảng chart chèn vào đây
// - {#datetime#} hệ thống điền "ngày dd tháng mm năm yyyy"; biến khác: nhập text hoặc gán filter dashboard
// - Section 1 cột; admin Publish template để người dùng chọn ở Download -> Export dashboard / Export chart
const path = require('path');
const { PORTRAIT_W, C, T, para, pageHeader, signatures, save } = require('./docx_kit');

(async () => {
  const head = pageHeader(PORTRAIT_W, { left: ['NGÂN HÀNG MẪU', T('ten_don_vi')], title: 'BÁO CÁO TỪ DASHBOARD',
    sub: [`Kỳ: ${T('ky_bao_cao')}`], right: ['Biểu mẫu: DB-01'] });
  await save(path.join(__dirname, '..', 'DB01_Dashboard_template.docx'), 'portrait', head, [
    para(T('dashboard')),
    para(`TP. Hồ Chí Minh, ${T('datetime')}`, { align: C, before: 200, italic: true }),
    ...signatures(PORTRAIT_W, ['Người lập', 'Lãnh đạo'], ['nguoi_lap', 'lanh_dao'], false),
  ]);
})().catch((e) => { console.error(e); process.exit(1); });
