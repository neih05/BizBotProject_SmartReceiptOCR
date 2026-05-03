export const employees = [];

export const invoices = [];

// Hệ thống tài khoản kế toán theo Thông tư 200 (các tài khoản phổ biến)
export const accounts = [
  { code: '111', name: 'Tiền mặt', type: 'Tài sản', level: 1 },
  { code: '1111', name: 'Tiền Việt Nam', type: 'Tài sản', level: 2 },
  { code: '112', name: 'Tiền gửi Ngân hàng', type: 'Tài sản', level: 1 },
  { code: '1121', name: 'Tiền Việt Nam', type: 'Tài sản', level: 2 },
  { code: '131', name: 'Phải thu của khách hàng', type: 'Tài sản', level: 1 },
  { code: '133', name: 'Thuế GTGT được khấu trừ', type: 'Tài sản', level: 1 },
  { code: '1331', name: 'Thuế GTGT được khấu trừ của hàng hóa, dịch vụ', type: 'Tài sản', level: 2 },
  { code: '141', name: 'Tạm ứng', type: 'Tài sản', level: 1 },
  { code: '152', name: 'Nguyên liệu, vật liệu', type: 'Tài sản', level: 1 },
  { code: '153', name: 'Công cụ, dụng cụ', type: 'Tài sản', level: 1 },
  { code: '211', name: 'Tài sản cố định hữu hình', type: 'Tài sản', level: 1 },
  { code: '331', name: 'Phải trả cho người bán', type: 'Nguồn vốn', level: 1 },
  { code: '333', name: 'Thuế và các khoản phải nộp Nhà nước', type: 'Nguồn vốn', level: 1 },
  { code: '3331', name: 'Thuế GTGT phải nộp', type: 'Nguồn vốn', level: 2 },
  { code: '334', name: 'Phải trả người lao động', type: 'Nguồn vốn', level: 1 },
  { code: '511', name: 'Doanh thu bán hàng và cung cấp dịch vụ', type: 'Doanh thu', level: 1 },
  { code: '641', name: 'Chi phí bán hàng', type: 'Chi phí', level: 1 },
  { code: '642', name: 'Chi phí quản lý doanh nghiệp', type: 'Chi phí', level: 1 },
  { code: '6421', name: 'Chi phí nhân viên quản lý', type: 'Chi phí', level: 2 },
  { code: '6422', name: 'Chi phí vật liệu quản lý', type: 'Chi phí', level: 2 },
  { code: '6423', name: 'Chi phí đồ dùng văn phòng', type: 'Chi phí', level: 2 },
  { code: '6424', name: 'Chi phí khấu hao TSCĐ', type: 'Chi phí', level: 2 },
  { code: '6425', name: 'Thuế, phí và lệ phí', type: 'Chi phí', level: 2 },
  { code: '6427', name: 'Chi phí dịch vụ mua ngoài', type: 'Chi phí', level: 2 },
  { code: '6428', name: 'Chi phí bằng tiền khác', type: 'Chi phí', level: 2 },
];

export const suppliers = [];

export const departments = [];

// Danh mục chi phí (tags) phổ biến trong nghiệp vụ kế toán
export const expenseTags = [
  { id: 1, name: 'Tiếp khách', description: 'Chi phí tiếp đãi khách hàng, đối tác' },
  { id: 2, name: 'Văn phòng phẩm', description: 'Giấy, bút, mực in, đồ dùng văn phòng' },
  { id: 3, name: 'Di chuyển', description: 'Taxi, Grab, xăng xe, phí gửi xe công tác' },
  { id: 4, name: 'Công tác phí', description: 'Vé máy bay, tàu xe, khách sạn đi công tác' },
  { id: 5, name: 'Ăn uống', description: 'Cơm trưa, nước uống phục vụ công việc' },
  { id: 6, name: 'Điện nước', description: 'Tiền điện, nước, internet văn phòng' },
  { id: 7, name: 'Thuê mặt bằng', description: 'Tiền thuê văn phòng, kho bãi' },
  { id: 8, name: 'Sửa chữa / Bảo trì', description: 'Sửa chữa tài sản, bảo dưỡng thiết bị' },
  { id: 9, name: 'Marketing', description: 'Quảng cáo, chạy ads, in ấn tờ rơi' },
  { id: 10, name: 'Khác', description: 'Các khoản chi phí chưa phân loại' },
];

export const formatCurrency = (value) => {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
};
