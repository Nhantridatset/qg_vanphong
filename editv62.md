# Danh sách Tên biến và Hàm trong Hệ thống (editv62.md)

*Lưu ý: Tài liệu này liệt kê các tên biến, hàm và lớp chính được định nghĩa hoặc sử dụng trong các file cốt lõi của dự án. Đây là một bản tóm tắt tập trung vào các thành phần chính, không phải là danh sách đầy đủ mọi định danh trong toàn bộ mã nguồn.*

## 1. `core/models.py`

### Tên lớp (Models)
- `CoQuan`
- `PhongBan`
- `HoSoCongViec`
- `KeHoach`
- `MocThoiGian`
- `NhiemVu`
- `BinhLuan`
- `TepDinhKem`
- `LichSuCongViec`
- `Notification`
- `CustomReport`
- `LoaiNhiemVu`
- `TruongDuLieu`
- `GiaTriTruongDuLieu`
- `GiaiNgan`
- `GoiThau`

### Tên trường (Fields) và Enum
- **`CoQuan`**: `name`
- **`PhongBan`**: `name`, `co_quan`
- **`HoSoCongViec`**:
    - `TrangThai` (Enum): `CHO_PHE_DUYET`, `DA_TU_CHOI`, `DA_DUYET`, `DANG_TRIEN_KHAI`, `TAM_DUNG`, `HOAN_THANH`, `DA_LUU_TRU`, `DA_HUY`
    - `ten_ho_so_cong_viec`, `ma_ho_so_cong_viec`, `mo_ta`, `trang_thai`, `phan_loai_linh_vuc`, `can_cu_phap_ly`, `ngay_bat_dau`, `ngay_ket_thuc`, `id_nguoi_quan_ly`, `id_don_vi_chu_tri`
- **`KeHoach`**:
    - `TrangThai` (Enum): `CHUA_BAT_DAU`, `DANG_THUC_HIEN`, `HOAN_THANH`, `BI_TRE`, `DA_DUYET`
    - `ten_ke_hoach`, `muc_tieu`, `trang_thai`, `thoi_gian_bat_dau`, `thoi_gian_ket_thuc`, `id_du_an`, `id_don_vi_thuc_hien`, `id_nguoi_phu_trach`
- **`MocThoiGian`**:
    - `TrangThai` (Enum): `CHUA_BAT_DAU`, `HOAN_THANH`, `BI_TRE`
    - `ten_moc`, `ngay_den_han`, `trang_thai`, `id_ke_hoach`
- **`NhiemVu`**:
    - `TrangThai` (Enum): `PENDING_ASSIGNMENT_APPROVAL`, `ASSIGNED`, `PENDING_COMPLETION_APPROVAL`, `COMPLETED`
    - `MucDoUuTien` (Enum): `KHAN`, `CAO`, `THUONG`, `THAP`
    - `RecurringFrequency` (Enum): `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`
    - `TrangThaiGiaHan` (Enum): `CHUA_DUYET`, `DA_DUYET`, `DA_TU_CHOI`
    - `ten_nhiem_vu`, `mo_ta`, `trang_thai`, `muc_do_uu_tien`, `ngay_bat_dau`, `ngay_ket_thuc`, `id_ke_hoach`, `id_nguoi_tao`, `id_nguoi_giao_viec`, `id_nguoi_thuc_hien`, `id_phong_ban_lien_quan`, `id_nhiem_vu_cha`, `thoi_gian_uoc_tinh`, `thoi_gian_thuc_te`, `thoi_gian_xu_ly`, `is_recurring`, `recurring_frequency`, `recurring_until`, `danh_gia_sao`, `loi_danh_gia`, `ngay_ket_thuc_de_xuat`, `ly_do_gia_han`, `trang_thai_gia_han`, `nguoi_duyet_gia_han`
- **`BinhLuan`**: `nhiem_vu`, `user`, `parent`, `noi_dung`, `timestamp`
- **`TepDinhKem`**: `file`, `uploader`, `nhiem_vu`, `ho_so_cong_viec`, `binh_luan`
- **`LichSuCongViec`**: `nhiem_vu`, `user`, `timestamp`, `mo_ta`, `details`
- **`Notification`**: `user`, `message`, `timestamp`, `is_read`, `related_task`, `related_ho_so_cong_viec`
- **`CustomReport`**: `name`, `description`, `model_name`, `fields_to_display`, `filters`, `created_by`, `created_at`
- **`LoaiNhiemVu`**: `name`
- **`TruongDuLieu`**: `name`, `data_type`
- **`GiaTriTruongDuLieu`**: `truong_du_lieu`, `value`, `nhiem_vu`, `ho_so_cong_viec`
- **`GiaiNgan`**: `name`, `amount`, `date`, `ho_so_cong_viec`
- **`GoiThau`**: `name`, `description`, `ho_so_cong_viec`

### Tên hàm (Methods)
- `__str__` (cho tất cả các Models)

## 2. `users/models.py`

### Tên lớp (Models)
- `CustomUser`

### Tên trường (Fields) và Enum
- **`CustomUser`**:
    - `Role` (Enum): `LANH_DAO_CO_QUAN`, `LANH_DAO_VAN_PHONG`, `LANH_DAO_PHONG`, `CHUYEN_VIEN_VAN_PHONG`, `CHUYEN_VIEN_PHONG`
    - `role`, `co_quan`, `phong_ban`, `zalo_user_id`

### Tên hàm (Methods)
- `__str__`

## 3. `core/forms.py`

### Tên lớp (Forms)
- `HoSoCongViecForm`
- `KeHoachForm`
- `MocThoiGianForm`
- `NhiemVuForm`
- `BinhLuanForm`
- `CoQuanForm`
- `PhongBanForm`
- `TepDinhKemForm`
- `LichSuCongViecForm`
- `TaskHandoverForm`
- `CustomReportForm`
- `LoaiNhiemVuForm`
- `TruongDuLieuForm`
- `GiaTriTruongDuLieuForm`
- `GiaiNganForm`
- `GoiThauForm`
- `ExtensionRequestForm`

### Tên hàm (Methods)
- `NhiemVuForm.__init__`
- `CustomReportForm.clean_fields_to_display`
- `CustomReportForm.clean_filters`

### Tên biến (Form Fields)
- `TaskHandoverForm`: `task`, `new_assignee`
- `CustomReportForm`: `fields_to_display`, `filters`

## 4. `core/views.py`

### Tên hàm (Functions)
- `home`
- `dashboard`
- `nhiemvu_kanban_view`
- `nhiemvu_calendar_view`
- `nhiemvu_calendar_data`
- `nhiemvu_gantt_view`
- `nhiemvu_gantt_data`
- `report_project_progress_view`
- `export_project_progress_pdf`
- `export_project_progress_excel`
- `notification_list`
- `mark_notification_as_read`
- `get_unread_notifications_count`
- `update_task_date_from_calendar`
- `task_handover_view`
- `approve_hosocongviec_view`
- `approve_kehoach_view`
- `approve_nhiemvu_view`
- `complete_and_rate_nhiemvu_view`
- `approve_assignment_view`
- `request_extension_view`

### Tên lớp (Class-Based Views)
- `CoQuanListView`, `CoQuanDetailView`, `CoQuanCreateView`, `CoQuanUpdateView`, `CoQuanDeleteView`
- `PhongBanListView`, `PhongBanDetailView`, `PhongBanCreateView`, `PhongBanUpdateView`, `PhongBanDeleteView`
- `HoSoCongViecListView`, `HoSoCongViecDetailView`, `HoSoCongViecCreateView`, `HoSoCongViecUpdateView`, `HoSoCongViecDeleteView`
- `KeHoachListView`, `KeHoachDetailView`, `KeHoachCreateView`, `KeHoachUpdateView`, `KeHoachDeleteView`
- `MocThoiGianListView`, `MocThoiGianDetailView`, `MocThoiGianCreateView`, `MocThoiGianUpdateView`, `MocThoiGianDeleteView`
- `NhiemVuListView`, `NhiemVuDetailView`, `NhiemVuCreateView`, `NhiemVuUpdateView`, `NhiemVuDeleteView`
- `TepDinhKemListView`, `TepDinhKemDetailView`, `TepDinhKemCreateView`, `TepDinhKemUpdateView`, `TepDinhKemDeleteView`
- `LichSuCongViecListView`, `LichSuCongViecDetailView`, `LichSuCongViecCreateView`, `LichSuCongViecUpdateView`, `LichSuCongViecDeleteView`
- `CustomReportListView`, `CustomReportDetailView`, `CustomReportCreateView`, `CustomReportUpdateView`, `CustomReportDeleteView`

### Tên biến cục bộ quan trọng (Important Local Variables)
- `user`, `context`, `today`, `tomorrow`, `nhiemvu`, `form`, `assignee`, `co_quan`, `phong_ban`, `message`, `events`, `data`, `buffer`, `p`, `workbook`, `worksheet`, `headers`, `col_num`, `header_title`, `cell`, `column_letter`, `response`, `task_id`, `new_start_str`, `new_end_str`, `e`, `hosocongviec`, `kehoach`, `rating`, `review`, `new_user`

## 5. `core/urls.py`

### Tên URL (URL Names)
- `home`
- `dashboard`
- `nhiemvu-kanban`
- `nhiemvu-calendar`
- `nhiemvu-calendar-data`
- `nhiemvu-gantt`
- `nhiemvu-gantt-data`
- `report-project-progress`
- `export-project-progress-pdf`
- `export-project-progress-excel`
- `notification-list`
- `mark-notification-as-read`
- `unread-notifications-count`
- `update-task-date-from-calendar`
- `task-handover`
- `hosocongviec-list`, `hosocongviec-detail`, `hosocongviec-create`, `hosocongviec-update`, `hosocongviec-delete`
- `kehoach-list`, `kehoach-detail`, `kehoach-create`, `kehoach-update`, `kehoach-delete`
- `mocthoigian-list`, `mocthoigian-detail`, `mocthoigian-create`, `mocthoigian-update`, `mocthoigian-delete`
- `nhiemvu-list`, `nhiemvu-detail`, `nhiemvu-create`, `nhiemvu-update`, `nhiemvu-delete`
- `approve-assignment`
- `coquan-list`, `coquan-detail`, `coquan-create`, `coquan-update`, `coquan-delete`
- `phongban-list`, `phongban-detail`, `phongban-create`, `phongban-update`, `phongban-delete`
- `tepdinhkem-list`, `tepdinhkem-detail`, `tepdinhkem-create`, `tepdinhkem-update`, `tepdinhkem-delete`
- `lichsucongviec-list`, `lichsucongviec-detail`, `lichsucongviec-create`, `lichsucongviec-update`, `lichsucongviec-delete`
- `customreport-list`, `customreport-create`, `customreport-detail`, `customreport-update`, `customreport-delete`
- `approve-hosocongviec`, `approve-kehoach`, `approve-nhiemvu`
- `complete-and-rate-nhiemvu`
- `request-extension`

## 6. `core/utils.py`

### Tên hàm (Functions)
- `send_notification_email`
- `create_notification`

### Tên biến (Parameters)
- `send_notification_email`: `recipient_email`, `subject`, `message`
- `create_notification`: `user`, `message`, `related_task`, `related_ho_so_cong_viec`
