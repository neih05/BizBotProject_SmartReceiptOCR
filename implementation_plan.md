# Kế hoạch Hoàn thiện Dự án BizBot (Dựa trên nhận xét của giảng viên & Thực tế doanh nghiệp)

## 1. Kết quả Audit Hiện trạng (Khung Dashboard & Database)

Sau khi kiểm tra lại toàn bộ mã nguồn:
*   **Về Web Dashboard:** Các bạn Hải và Hiền đã dựng được bộ khung Dashboard khá tốt bằng **React + Vite**. Đã có các trang `Employees.jsx`, `InvoiceManagement.jsx`, `Export.jsx`, `Overview.jsx`. Dashboard đã có khả năng gọi API đến backend (FastAPI - `api.py`) để lấy dữ liệu.
*   **Về Database:** Cấu trúc SQLite (`invoices.db`) có các bảng `invoices`, `users`, và `employees`. Hiện tại bảng `employees` đang có cột `employee_id` (thực chất đang chứa dãy số giống Telegram ID). **Tuy nhiên**, phần Bot chưa kết nối logic này chuẩn xác. 
*   **Điểm còn thiếu/chưa đồng bộ:** 
    *   Bot đang tự động cho phép *tất cả mọi người* dùng bot (tự lưu tên Telegram của họ vào DB).
    *   Dashboard đang dùng ảnh minh họa (placeholder) thay vì hiển thị hình ảnh hóa đơn thật từ Telegram.
    *   Chưa có chức năng quản lý Danh mục (Tags) trên Web.

## 2. Các công việc cần làm ngay (Theo nhận xét của Thầy)

Dựa trên giải thích của bạn về ý của thầy, đây là cách chúng ta sẽ sửa lại:

### 2.1. Quản lý ID Nhân viên (Telegram ID) trong Database
*   **Vấn đề:** Hiện tại ai chat với bot cũng được. Và tên lưu vào hệ thống đang bị phụ thuộc vào tên hiển thị trên Telegram (VD: "Hoa Hồng nhỏ").
*   **Giải pháp:** 
    *   Kế toán (Admin) sẽ nhập sẵn các `Telegram ID` của nhân viên vào bảng `employees` trong Database kèm theo **Tên Thật** (VD: Đào Thanh Hiền).
    *   Khi có người chat với bot, bot sẽ lấy ID của người đó dò trong DB. **NẾU CÓ**, bot sẽ chào "Xin chào Đào Thanh Hiền" (cho dù nick Tele của bạn ấy là Hoa Hồng nhỏ) và cho phép sử dụng. **NẾU KHÔNG CÓ**, bot sẽ từ chối: "Bạn chưa được cấp quyền sử dụng nội bộ".
    *   Việc này giúp Kế toán quản lý bằng **Tên Thật**, độc lập hoàn toàn với tên nick Telegram.

### 2.2. Hoàn thiện Web Dashboard cho Kế toán
*   Tạo thêm một tab/trang **Quản lý Danh mục (Tags)** trên Web để Kế toán thêm/xóa loại chi phí.
*   Đảm bảo `InvoiceManagement.jsx` tải được **ảnh thật** của hóa đơn do staff gửi qua Telegram (xóa cái hình minh họa đi).
*   Giao diện Dashboard hiện tại đã có khung cho các tính năng /pending, /users, /export.

### 2.3. Fix lỗi trùng lặp đơn & Sửa luồng nhập tay (/expense)
*   **Trùng lặp:** Lệnh `/expense` hiện tại đang đẩy thẳng vào database mà bỏ qua bước check trùng lặp! Hàm check khi gửi ảnh thì chỉ "cảnh báo" chứ vẫn cho lưu. Tôi sẽ code khóa **chặn lưu hóa đơn trùng lặp**.
*   **Bỏ chọn Danh mục:** Sửa lại cú pháp lệnh `/expense` trên bot, staff **chỉ cần gõ** `/expense 50000 KFC` là xong. Bỏ yêu cầu nhập `- [Danh mục]`. Kế toán sẽ là người chọn danh mục trên Web.

### 2.4. Quyền Admin
*   Admin vẫn dùng bot để nộp hóa đơn chi tiêu như staff bình thường. Các lệnh quản lý đã được gỡ khỏi bot thành công và sẽ được thao tác hoàn toàn trên Web Dashboard.

---

## 3. Đánh giá tính thực tiễn (Business Realities) - Để đưa sản phẩm ra thị trường

Khi đưa sản phẩm SaaS này ra thị trường, các doanh nghiệp (B2B) sẽ yêu cầu sự bảo mật và quy trình chặt chẽ. Dưới đây là những tính năng **bắt buộc phải bổ sung** để sản phẩm dùng được trong thực tế:

1. **Hệ thống Login cho Web Dashboard:** Web hiện tại ai có link là vào được. Thực tế bắt buộc phải có màn hình Đăng nhập (Username/Password) bảo mật cho Kế toán.
2. **Quản lý Nhân sự (CRUD) trên Web:** Phải có tính năng để Kế toán tự thêm/sửa/xóa thông tin nhân viên (gồm Tên thật và Telegram ID của họ) trên trang Web, thay vì phải hardcode vào Database như hiện nay.
3. **Hiển thị hình ảnh OCR gốc:** Kế toán phải nhìn thấy Bill gốc kế bên dữ liệu AI bóc tách để đối soát. Yêu cầu tải ảnh từ máy chủ Telegram về Backend.
4. **Cơ chế lưu trữ (Storage):** Telegram chỉ cho phép lấy file tạm thời bằng `file_id`. Về lâu dài (luật kế toán cần lưu chứng từ 5-10 năm), ứng dụng phải tự download ảnh đó về lưu trên server nội bộ hoặc ổ cứng đám mây (S3).
5. **Gán phòng ban (Cost Center):** Khi duyệt hóa đơn, phải biết chi phí này thuộc phòng ban nào (Marketing, IT, Hành chính) để cuối tháng ra báo cáo.

---

## User Review Required

> [!IMPORTANT]
> Cảm ơn bạn đã giải thích rõ ý của thầy! Tôi đã cập nhật lại kế hoạch. Bạn xem có đúng ý bạn chưa nhé. Nếu bạn **Approve**, tôi sẽ tiến hành:
> 1. Sửa bot để chỉ cho phép các `Telegram ID` đã có trong DB sử dụng, và tự động map đúng "Tên Thật".
> 2. Fix triệt để bug trùng lặp hóa đơn và bỏ vụ bắt buộc chọn "Danh mục" khi gõ `/expense`.
> 3. Nối API để Web tải được ảnh thật từ Telegram.
> 4. Làm thêm màn hình quản lý Danh mục (Tags) trên Web.

## Open Questions

> [!TIP]
> Bạn có muốn tôi thiết kế thêm một màn hình **Đăng nhập (Login)** và chức năng **Thêm nhân viên** trên Dashboard luôn để sản phẩm trông giống "hàng thật" (có tính thị trường) hơn không? Hay chỉ tập trung xử lý các lỗi của Bot trước?
