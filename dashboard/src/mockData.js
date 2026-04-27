export const employees = [
  { id: 1, name: 'Nguyễn Minh Nguyệt', nickname: 'Nguyệt', empCode: 'NV001', department: 'Hành chính', telegramId: '6200223111', invoicesSent: 45, totalValue: 12500000, status: 'approved' },
  { id: 2, name: 'Đào Thanh Hiền', nickname: 'Hoa Hồng nhỏ', empCode: 'NV002', department: 'Sales', telegramId: '8100040764', invoicesSent: 120, totalValue: 45000000, status: 'approved' },
  { id: 3, name: 'Đinh Thị Hải', nickname: 'Hải', empCode: 'NV003', department: 'Kế toán', telegramId: '8747576383', invoicesSent: 12, totalValue: 3200000, status: 'approved' },
  { id: 4, name: 'Lê Văn Nam', nickname: 'Nam Tồ', empCode: 'NV004', department: 'IT', telegramId: '123456789', invoicesSent: 5, totalValue: 1500000, status: 'pending' },
  { id: 5, name: 'Trần Thị Mai', nickname: 'Mai Xinh', empCode: 'NV005', department: 'Marketing', telegramId: '987654321', invoicesSent: 30, totalValue: 28000000, status: 'approved' },
  { id: 6, name: 'Phạm Đức Anh', nickname: 'Anh Còi', empCode: 'NV006', department: 'Sales', telegramId: '456123789', invoicesSent: 0, totalValue: 0, status: 'pending' },
  { id: 7, name: 'Hoàng Kim Dung', nickname: 'Dung Beo', empCode: 'NV007', department: 'Hành chính', telegramId: '789123456', invoicesSent: 8, totalValue: 4200000, status: 'approved' },
  { id: 8, name: 'Vũ Hải Đăng', nickname: 'Đăng ML', empCode: 'NV008', department: 'Marketing', telegramId: '321654987', invoicesSent: 15, totalValue: 18500000, status: 'approved' },
];

export const invoices = [
  { id: 'INV-2026-001', date: '25/04/2026', sender: 'Đào Thanh Hiền', supplier: 'Highlands Coffee', amount: 150000, status: 'pending', ocr: { taxCode: '0101234567', invNo: '0001234', category: 'Tiếp khách', taxAmount: 12000 } },
  { id: 'INV-2026-002', date: '26/04/2026', sender: 'Nguyễn Minh Nguyệt', supplier: 'Văn phòng phẩm Hồng Hà', amount: 450000, status: 'approved', ocr: { taxCode: '0107654321', invNo: '0005678', category: 'Văn phòng phẩm', taxAmount: 36000 } },
  { id: 'INV-2026-003', date: '27/04/2026', sender: 'Đinh Thị Hải', supplier: 'Grab', amount: 85000, status: 'processing', ocr: { taxCode: '0108888888', invNo: '0009999', category: 'Di chuyển', taxAmount: 6800 } },
  { id: 'INV-2026-004', date: '24/04/2026', sender: 'Trần Thị Mai', supplier: 'Nhà hàng Làng Ngói', amount: 2500000, status: 'rejected', ocr: { taxCode: '0102223334', invNo: '0001111', category: 'Tiếp khách', taxAmount: 200000 } },
  { id: 'INV-2026-005', date: '27/04/2026', sender: 'Lê Văn Nam', supplier: 'GearVN', amount: 1250000, status: 'pending', ocr: { taxCode: '0312345678', invNo: '0003333', category: 'Mua sắm vật tư', taxAmount: 100000 } },
  { id: 'INV-2026-006', date: '22/04/2026', sender: 'Vũ Hải Đăng', supplier: 'Facebook Ads', amount: 5000000, status: 'approved', ocr: { taxCode: 'N/A', invNo: 'FB-98765', category: 'Khác', taxAmount: 0 } },
  { id: 'INV-2026-007', date: '23/04/2026', sender: 'Hoàng Kim Dung', supplier: 'Be Group', amount: 45000, status: 'approved', ocr: { taxCode: '0109999999', invNo: '0004444', category: 'Di chuyển', taxAmount: 3600 } },
  { id: 'INV-2026-008', date: '26/04/2026', sender: 'Đào Thanh Hiền', supplier: 'Nhà hàng Sen Tây Hồ', amount: 8400000, status: 'processing', ocr: { taxCode: '0105556667', invNo: '0002222', category: 'Tiếp khách', taxAmount: 672000 } },
  { id: 'INV-2026-009', date: '21/04/2026', sender: 'Nguyễn Minh Nguyệt', supplier: 'Bưu điện VNPost', amount: 120000, status: 'approved', ocr: { taxCode: '0101112223', invNo: '0007777', category: 'Hành chính', taxAmount: 9600 } },
  { id: 'INV-2026-010', date: '27/04/2026', sender: 'Đinh Thị Hải', supplier: 'Tiki Trading', amount: 890000, status: 'pending', ocr: { taxCode: '0313334445', invNo: '0008888', category: 'Văn phòng phẩm', taxAmount: 71200 } },
  { id: 'INV-2026-011', date: '20/04/2026', sender: 'Trần Thị Mai', supplier: 'Vietnam Airlines', amount: 3500000, status: 'approved', ocr: { taxCode: '0100107518', invNo: '0005555', category: 'Công tác phí', taxAmount: 280000 } },
  { id: 'INV-2026-012', date: '19/04/2026', sender: 'Lê Văn Nam', supplier: 'Xanh SM', amount: 155000, status: 'approved', ocr: { taxCode: '0110260408', invNo: '0006666', category: 'Di chuyển', taxAmount: 12400 } },
  { id: 'INV-2026-013', date: '25/04/2026', sender: 'Hoàng Kim Dung', supplier: 'WinMart', amount: 320000, status: 'rejected', ocr: { taxCode: '0108881111', invNo: '0001010', category: 'Khác', taxAmount: 25600 } },
  { id: 'INV-2026-014', date: '26/04/2026', sender: 'Vũ Hải Đăng', supplier: 'Công ty Tổ chức Sự kiện ABC', amount: 15000000, status: 'processing', ocr: { taxCode: '0103332221', invNo: '0001212', category: 'Marketing', taxAmount: 1200000 } },
  { id: 'INV-2026-015', date: '27/04/2026', sender: 'Đào Thanh Hiền', supplier: "Pizza 4P's", amount: 950000, status: 'pending', ocr: { taxCode: '0312341234', invNo: '0001313', category: 'Tiếp khách', taxAmount: 76000 } }
];

export const accounts = [
  { code: '111', name: 'Tiền mặt', type: 'Tài sản', level: 1 },
  { code: '1111', name: 'Tiền Việt Nam', type: 'Tài sản', level: 2 },
  { code: '112', name: 'Tiền gửi Ngân hàng', type: 'Tài sản', level: 1 },
  { code: '1121', name: 'Tiền Việt Nam', type: 'Tài sản', level: 2 },
  { code: '131', name: 'Phải thu của khách hàng', type: 'Tài sản', level: 1 },
  { code: '133', name: 'Thuế GTGT được khấu trừ', type: 'Tài sản', level: 1 },
  { code: '1331', name: 'Thuế GTGT được khấu trừ của hàng hóa, dịch vụ', type: 'Tài sản', level: 2 },
  { code: '152', name: 'Nguyên liệu, vật liệu', type: 'Tài sản', level: 1 },
  { code: '211', name: 'Tài sản cố định hữu hình', type: 'Tài sản', level: 1 },
  { code: '331', name: 'Phải trả cho người bán', type: 'Nguồn vốn', level: 1 },
  { code: '333', name: 'Thuế và các khoản phải nộp Nhà nước', type: 'Nguồn vốn', level: 1 },
  { code: '511', name: 'Doanh thu bán hàng và cung cấp dịch vụ', type: 'Doanh thu', level: 1 },
  { code: '641', name: 'Chi phí bán hàng', type: 'Chi phí', level: 1 },
  { code: '642', name: 'Chi phí quản lý doanh nghiệp', type: 'Chi phí', level: 1 },
  { code: '6422', name: 'Chi phí vật liệu quản lý', type: 'Chi phí', level: 2 },
  { code: '6427', name: 'Chi phí dịch vụ mua ngoài', type: 'Chi phí', level: 2 },
  { code: '6428', name: 'Chi phí bằng tiền khác', type: 'Chi phí', level: 2 }
];

export const suppliers = [
  { name: 'Công ty Cổ phần Highlands Coffee', taxCode: '0101234567', invoicesCount: 15, lastTransaction: '25/04/2026' },
  { name: 'Công ty CP Văn phòng phẩm Hồng Hà', taxCode: '0107654321', invoicesCount: 4, lastTransaction: '26/04/2026' },
  { name: 'Công ty TNHH Grab', taxCode: '0108888888', invoicesCount: 42, lastTransaction: '27/04/2026' },
  { name: 'Nhà hàng Làng Ngói', taxCode: '0102223334', invoicesCount: 2, lastTransaction: '24/04/2026' },
  { name: 'Công ty TNHH GearVN', taxCode: '0312345678', invoicesCount: 1, lastTransaction: '27/04/2026' },
  { name: 'Công ty Cổ phần Hàng không Việt Nam', taxCode: '0100107518', invoicesCount: 8, lastTransaction: '20/04/2026' },
  { name: 'Công ty CP Di chuyển Xanh và Thông minh GSM', taxCode: '0110260408', invoicesCount: 25, lastTransaction: '19/04/2026' },
  { name: 'Công ty CP Dịch vụ Thương mại Tổng hợp WinCommerce', taxCode: '0108881111', invoicesCount: 12, lastTransaction: '25/04/2026' },
  { name: "Pizza 4P's", taxCode: '0312341234', invoicesCount: 6, lastTransaction: '27/04/2026' }
];

export const departments = [
  { name: 'Sales', budget: 100000000, spent: 85000000, status: 'warning' },
  { name: 'Marketing', budget: 50000000, spent: 55000000, status: 'danger' },
  { name: 'IT', budget: 30000000, spent: 15000000, status: 'safe' },
  { name: 'Hành chính', budget: 20000000, spent: 12000000, status: 'safe' },
  { name: 'Kế toán', budget: 10000000, spent: 5000000, status: 'safe' }
];

export const weeklyChartData = [
  { name: 'Tuần 1', 'Tiếp khách': 4000000, 'Văn phòng phẩm': 2400000, 'Di chuyển': 2400000 },
  { name: 'Tuần 2', 'Tiếp khách': 3000000, 'Văn phòng phẩm': 1398000, 'Di chuyển': 2210000 },
  { name: 'Tuần 3', 'Tiếp khách': 2000000, 'Văn phòng phẩm': 9800000, 'Di chuyển': 2290000 },
  { name: 'Tuần 4', 'Tiếp khách': 2780000, 'Văn phòng phẩm': 3908000, 'Di chuyển': 2000000 },
];

export const categoryPieData = [
  { name: 'Văn phòng phẩm', value: 400 },
  { name: 'Tiếp khách', value: 300 },
  { name: 'Di chuyển', value: 300 },
  { name: 'Công tác phí', value: 200 },
  { name: 'Khác', value: 50 },
];

export const formatCurrency = (value) => {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
};
