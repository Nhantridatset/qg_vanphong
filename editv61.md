# Nhật ký thay đổi phiên làm việc (editv61.md)

Tài liệu này ghi lại các thay đổi được thực hiện trong phiên làm việc hiện tại để rà soát và cập nhật hệ thống theo tài liệu `v6.md`.

## 1. Cập nhật Nền tảng (Giai đoạn 1)

### 1.1. `users/models.py` (Model `CustomUser`)
-   **Thay đổi vai trò:** Cập nhật `CustomUser.Role` enum để khớp với `v6.md`, bao gồm:
    -   `LANH_DAO_CO_QUAN`
    -   `LANH_DAO_VAN_PHONG`
    -   `LANH_DAO_PHONG`
    -   `CHUYEN_VIEN_VAN_PHONG`
    -   `CHUYEN_VIEN_PHONG`
-   Loại bỏ các vai trò cũ không còn sử dụng (`ADMIN_TCI_CAO`, `ADMIN_DON_VI`).

### 1.2. `core/models.py` (Model `NhiemVu`)
-   **Cập nhật trạng thái:** Thay thế `TrangThai` enum bằng các trạng thái mới từ `v6.md`:
    -   `PENDING_ASSIGNMENT_APPROVAL`
    -   `ASSIGNED`
    -   `PENDING_COMPLETION_APPROVAL`
    -   `COMPLETED`
-   **Thêm trường mới cho Nhiệm vụ:**
    -   `id_nguoi_tao`: ForeignKey đến `CustomUser` (Người tạo nhiệm vụ).
    -   `id_nguoi_giao_viec`: ForeignKey đến `CustomUser` (Người giao nhiệm vụ).
    -   `id_phong_ban_lien_quan`: ForeignKey đến `PhongBan` (Phòng ban liên quan đến nhiệm vụ).
-   **Thêm trường mới cho yêu cầu gia hạn:**
    -   `ngay_ket_thuc_de_xuat`: DateTimeField (Ngày hết hạn mới được đề xuất).
    -   `ly_do_gia_han`: TextField (Lý do xin gia hạn).
    -   `trang_thai_gia_han`: CharField với các lựa chọn (`CHUA_DUYET`, `DA_DUYET`, `DA_TU_CHOI`).
    -   `nguoi_duyet_gia_han`: ForeignKey đến `CustomUser` (Người đã duyệt/từ chối yêu cầu gia hạn).

## 2. Triển khai Luồng Giao việc Đặc biệt (Giai đoạn 2, Phần 1)

### 2.1. `core/forms.py`
-   **Dọn dẹp mã trùng lặp:** Loại bỏ các định nghĩa lớp trùng lặp trong file.
-   **`NhiemVuForm`:**
    -   Chuyển từ `fields = '__all__'` sang liệt kê các trường cụ thể.
    -   Thêm phương thức `__init__` để truyền `request.user` vào form.
    -   Triển khai logic lọc `queryset` cho `id_nguoi_thuc_hien` (người nhận) và `id_ke_hoach` (kế hoạch) dựa trên vai trò của người dùng hiện tại và quy tắc giao việc.
-   **`ExtensionRequestForm`:** Thêm form mới để xử lý yêu cầu gia hạn nhiệm vụ.

### 2.2. `core/views.py`
-   **Khôi phục file:** Đảm bảo file `core/views.py` được khôi phục về trạng thái đúng sau các lỗi trước đó.
-   **`dashboard` view:** Cập nhật logic truy vấn dữ liệu cho vai trò `LANH_DAO_CO_QUAN` để hiển thị công việc hết hạn trong 1 ngày và công việc sắp đến hạn.
-   **`NhiemVuCreateView`:**
    -   Tự động gán `id_nguoi_tao` và `id_nguoi_giao_viec` là người dùng hiện tại.
    -   Thiết lập `trang_thai` ban đầu của nhiệm vụ (`PENDING_ASSIGNMENT_APPROVAL` hoặc `ASSIGNED`) dựa trên quy tắc giao việc đặc biệt (Chuyên viên Văn phòng giao cho Lãnh đạo Phòng).
    -   Thiết lập `id_phong_ban_lien_quan` dựa trên phòng ban của người nhận nhiệm vụ.
    -   Thêm ghi nhật ký kiểm toán (`LichSuCongViec`) khi nhiệm vụ được tạo.
    -   Gửi thông báo in-app (`Notification`) đến `Lãnh đạo Cơ quan` và `Lãnh đạo Văn phòng` khi nhiệm vụ cần phê duyệt giao.
-   **`approve_assignment_view`:**
    -   Thêm view mới để xử lý việc phê duyệt nhiệm vụ ở trạng thái `PENDING_ASSIGNMENT_APPROVAL`.
    -   Kiểm tra quyền phê duyệt (chỉ `Lãnh đạo Cơ quan` hoặc `Lãnh đạo Văn phòng`).
    -   Chuyển trạng thái nhiệm vụ sang `ASSIGNED` sau khi phê duyệt.
    -   Thêm ghi nhật ký kiểm toán (`LichSuCongViec`) khi nhiệm vụ được phê duyệt.
    -   Gửi thông báo in-app (`Notification`) đến người giao việc và người thực hiện khi nhiệm vụ được phê duyệt.
-   **`request_extension_view`:** Thêm view mới để xử lý yêu cầu gia hạn nhiệm vụ.
    -   Kiểm tra quyền (chỉ người thực hiện nhiệm vụ).
    -   Kiểm tra trạng thái nhiệm vụ (chỉ khi `ASSIGNED`).
    -   Lưu `ngay_ket_thuc_de_xuat`, `ly_do_gia_han`, và đặt `trang_thai_gia_han` là `CHUA_DUYET`.
    -   Thêm ghi nhật ký kiểm toán (`LichSuCongViec`) khi yêu cầu gia hạn được gửi.
    -   Gửi thông báo in-app (`Notification`) đến người giao việc khi có yêu cầu gia hạn.
-   **Imports:** Đảm bảo các import cần thiết (`CustomUser`, `UserPassesTestMixin`, `create_notification`) được thêm vào.

### 2.3. `core/templates/core/dashboard.html`
-   Thêm các khối hiển thị "Công việc hết hạn vào ngày mai" và "Công việc sắp đến hạn" cho vai trò `LANH_DAO_CO_QUAN`.

### 2.4. `core/templates/core/nhiemvu_detail.html`
-   Thêm nút "Phê duyệt giao việc" hiển thị có điều kiện khi nhiệm vụ ở trạng thái `PENDING_ASSIGNMENT_APPROVAL` và người dùng có quyền.

### 2.5. `core/templates/core/nhiemvu_approve_assignment.html`
-   Tạo template mới để hiển thị giao diện phê duyệt giao nhiệm vụ.

### 2.6. `core/urls.py`
-   Thêm URL pattern cho `approve-assignment`.
-   Thêm URL pattern cho `request-extension`.

### 2.7. `core/utils.py`
-   Thêm hàm tiện ích `create_notification` để tạo thông báo in-app.
