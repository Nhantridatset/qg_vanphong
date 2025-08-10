from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class CoQuan(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class PhongBan(models.Model):
    name = models.CharField(max_length=255)
    co_quan = models.ForeignKey(CoQuan, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class HoSoCongViec(models.Model):
    class TrangThai(models.TextChoices):
        CHO_PHE_DUYET = 'CHO_PHE_DUYET', _('Chờ phê duyệt')
        DA_TU_CHOI = 'DA_TU_CHOI', _('Đã từ chối')
        DA_DUYET = 'DA_DUYET', _('Đã duyệt')
        DANG_TRIEN_KHAI = 'DANG_TRIEN_KHAI', _('Đang triển khai')
        TAM_DUNG = 'TAM_DUNG', _('Tạm dừng')
        HOAN_THANH = 'HOAN_THANH', _('Hoàn thành')
        DA_LUU_TRU = 'DA_LUU_TRU', _('Đã lưu trữ')
        DA_HUY = 'DA_HUY', _('Đã hủy')

    ten_ho_so_cong_viec = models.CharField(max_length=255, verbose_name=_('Tên hồ sơ công việc'))
    ma_ho_so_cong_viec = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name=_('Mã hồ sơ công việc'))
    mo_ta = models.TextField(verbose_name=_('Mô tả'))
    trang_thai = models.CharField(max_length=50, choices=TrangThai.choices, default=TrangThai.CHO_PHE_DUYET, verbose_name=_('Trạng thái'))
    phan_loai_linh_vuc = models.CharField(max_length=255, verbose_name=_('Phân loại lĩnh vực'))
    can_cu_phap_ly = models.TextField(verbose_name=_('Căn cứ pháp lý'))
    ngay_bat_dau = models.DateTimeField(verbose_name=_('Ngày bắt đầu'), null=True, blank=True)
    ngay_ket_thuc = models.DateTimeField(verbose_name=_('Ngày kết thúc'), null=True, blank=True)
    id_nguoi_quan_ly = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='du_an_quan_ly', verbose_name=_('Người quản lý'))
    id_don_vi_chu_tri = models.ForeignKey(PhongBan, on_delete=models.SET_NULL, null=True, verbose_name=_('Đơn vị chủ trì'))

    def __str__(self):
        return self.ten_ho_so_cong_viec

class KeHoach(models.Model):
    class TrangThai(models.TextChoices):
        CHUA_BAT_DAU = 'CHUA_BAT_DAU', _('Chưa bắt đầu')
        DANG_THUC_HIEN = 'DANG_THUC_HIEN', _('Đang thực hiện')
        HOAN_THANH = 'HOAN_THANH', _('Hoàn thành')
        BI_TRE = 'BI_TRE', _('Bị trễ')
        DA_DUYET = 'DA_DUYET', _('Đã duyệt')

    ten_ke_hoach = models.CharField(max_length=255, verbose_name=_('Tên kế hoạch'))
    muc_tieu = models.TextField(verbose_name=_('Mục tiêu'))
    trang_thai = models.CharField(max_length=50, choices=TrangThai.choices, default=TrangThai.CHUA_BAT_DAU, verbose_name=_('Trạng thái'))
    thoi_gian_bat_dau = models.DateTimeField(verbose_name=_('Thời gian bắt đầu'))
    thoi_gian_ket_thuc = models.DateTimeField(verbose_name=_('Thời gian kết thúc'))
    id_du_an = models.ForeignKey(HoSoCongViec, on_delete=models.CASCADE, related_name='ke_hoach', verbose_name=_('Hồ sơ công việc'))
    id_don_vi_thuc_hien = models.ForeignKey(PhongBan, on_delete=models.SET_NULL, null=True, verbose_name=_('Đơn vị thực hiện'))
    id_nguoi_phu_trach = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ke_hoach_phu_trach', verbose_name=_('Người phụ trách'))

    def __str__(self):
        return self.ten_ke_hoach

class MocThoiGian(models.Model):
    class TrangThai(models.TextChoices):
        CHUA_BAT_DAU = 'CHUA_BAT_DAU', _('Chưa bắt đầu')
        HOAN_THANH = 'HOAN_THANH', _('Hoàn thành')
        BI_TRE = 'BI_TRE', _('Bị trễ')

    ten_moc = models.CharField(max_length=255, verbose_name=_('Tên mốc'))
    ngay_den_han = models.DateTimeField(verbose_name=_('Ngày đến hạn'))
    trang_thai = models.CharField(max_length=50, choices=TrangThai.choices, default=TrangThai.CHUA_BAT_DAU, verbose_name=_('Trạng thái'))
    id_ke_hoach = models.ForeignKey(KeHoach, on_delete=models.CASCADE, related_name='moc_thoi_gian', verbose_name=_('Kế hoạch'))

    def __str__(self):
        return self.ten_moc

class NhiemVu(models.Model):
    class TrangThai(models.TextChoices):
        NV_CHO = 'NV_CHO', _('Chờ duyệt giao')
        DANG_THUC_HIEN = 'DANG_THUC_HIEN', _('Đang thực hiện')
        YEU_CAU_LAM_LAI = 'YEU_CAU_LAM_LAI', _('Yêu cầu làm lại')
        DA_DUYET = 'DA_DUYET', _('Đã duyệt')
        HOAN_THANH = 'HOAN_THANH', _('Hoàn thành')
        NV_TTC = 'NV_TTC', _('Bị từ chối')

    class MucDoUuTien(models.TextChoices):
        KHAN = 'KHAN', _('Khẩn')
        CAO = 'CAO', _('Cao')
        THUONG = 'THUONG', _('Thường')
        THAP = 'THAP', _('Thấp')

    class RecurringFrequency(models.TextChoices):
        DAILY = 'DAILY', _('Hàng ngày')
        WEEKLY = 'WEEKLY', _('Hàng tuần')
        MONTHLY = 'MONTHLY', _('Hàng tháng')
        YEARLY = 'YEARLY', _('Hàng năm')

    ten_nhiem_vu = models.CharField(max_length=255, verbose_name=_('Tên nhiệm vụ'))
    mo_ta = models.TextField(verbose_name=_('Mô tả'))
    trang_thai = models.CharField(max_length=50, choices=TrangThai.choices, default=TrangThai.NV_CHO, verbose_name=_('Trạng thái'))
    muc_do_uu_tien = models.CharField(max_length=50, choices=MucDoUuTien.choices, default=MucDoUuTien.THUONG, verbose_name=_('Mức độ ưu tiên'))
    ngay_bat_dau = models.DateTimeField(verbose_name=_('Ngày bắt đầu'), null=True, blank=True)
    ngay_ket_thuc = models.DateTimeField(verbose_name=_('Ngày kết thúc'), null=True, blank=True)
    id_ke_hoach = models.ForeignKey(KeHoach, on_delete=models.CASCADE, related_name='nhiem_vu', verbose_name=_('Kế hoạch'))
    id_nguoi_thuc_hien = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='nhiem_vu_thuc_hien', verbose_name=_('Người thực hiện'))
    id_nhiem_vu_cha = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_tasks', verbose_name=_('Nhiệm vụ cha'))
    thoi_gian_uoc_tinh = models.FloatField(null=True, blank=True, verbose_name=_('Thời gian ước tính (giờ)'))
    thoi_gian_thuc_te = models.FloatField(null=True, blank=True, verbose_name=_('Thời gian thực tế (giờ)'))
    thoi_gian_xu_ly = models.FloatField(null=True, blank=True, verbose_name=_('Thời gian xử lý (giờ)'))

    is_recurring = models.BooleanField(default=False, verbose_name=_('Nhiệm vụ lặp lại'))
    recurring_frequency = models.CharField(max_length=20, choices=RecurringFrequency.choices, null=True, blank=True, verbose_name=_('Tần suất lặp lại'))
    recurring_until = models.DateTimeField(null=True, blank=True, verbose_name=_('Lặp lại đến ngày'))

    danh_gia_sao = models.IntegerField(null=True, blank=True, choices=[(i, str(i)) for i in range(1, 6)], verbose_name=_('Đánh giá sao'))
    loi_danh_gia = models.TextField(null=True, blank=True, verbose_name=_('Lời đánh giá'))

    def __str__(self):
        return self.ten_nhiem_vu

class BinhLuan(models.Model):
    nhiem_vu = models.ForeignKey(NhiemVu, on_delete=models.CASCADE, related_name='binh_luan')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='binh_luan')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    noi_dung = models.TextField(verbose_name=_('Nội dung'))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Thời gian'))

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'Bình luận của {self.user.username} trên "{self.nhiem_vu.ten_nhiem_vu}"'

class TepDinhKem(models.Model):
    file = models.FileField(upload_to='attachments/')
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nhiem_vu = models.ForeignKey(NhiemVu, on_delete=models.CASCADE, null=True, blank=True, related_name='tep_dinh_kem')
    ho_so_cong_viec = models.ForeignKey(HoSoCongViec, on_delete=models.CASCADE, null=True, blank=True, related_name='tep_dinh_kem')
    binh_luan = models.ForeignKey(BinhLuan, on_delete=models.CASCADE, null=True, blank=True, related_name='tep_dinh_kem')

class LichSuCongViec(models.Model):
    nhiem_vu = models.ForeignKey(NhiemVu, on_delete=models.CASCADE, related_name='lich_su', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    mo_ta = models.CharField(max_length=255, verbose_name=_('Mô tả hành động'), null=True)
    details = models.JSONField(null=True, blank=True, verbose_name=_('Chi tiết'))

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.mo_ta} on {self.nhiem_vu}'

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_task = models.ForeignKey(NhiemVu, on_delete=models.SET_NULL, null=True, blank=True)
    related_ho_so_cong_viec = models.ForeignKey(HoSoCongViec, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'Notification for {self.user.username}: {self.message[:50]}...'

class CustomReport(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Tên báo cáo'))
    description = models.TextField(blank=True, verbose_name=_('Mô tả'))
    model_name = models.CharField(max_length=100, verbose_name=_('Model nguồn')) # e.g., 'DuAn', 'NhiemVu'
    fields_to_display = models.JSONField(verbose_name=_('Các trường hiển thị')) # List of field names
    filters = models.JSONField(blank=True, null=True, verbose_name=_('Bộ lọc')) # Dictionary of filters
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_('Người tạo'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Thời gian tạo'))

    def __str__(self):
        return self.name


class LoaiNhiemVu(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Tên loại nhiệm vụ'))

    def __str__(self):
        return self.name


class TruongDuLieu(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Tên trường dữ liệu'))
    data_type = models.CharField(max_length=50, verbose_name=_('Kiểu dữ liệu')) # e.g., 'text', 'number', 'date'

    def __str__(self):
        return self.name


class GiaTriTruongDuLieu(models.Model):
    truong_du_lieu = models.ForeignKey(TruongDuLieu, on_delete=models.CASCADE, verbose_name=_('Trường dữ liệu'))
    value = models.TextField(verbose_name=_('Giá trị'))
    nhiem_vu = models.ForeignKey(NhiemVu, on_delete=models.CASCADE, null=True, blank=True, related_name='gia_tri_truong_du_lieu', verbose_name=_('Nhiệm vụ'))
    ho_so_cong_viec = models.ForeignKey(HoSoCongViec, on_delete=models.CASCADE, null=True, blank=True, related_name='gia_tri_truong_du_lieu', verbose_name=_('Hồ sơ công việc'))

    def __str__(self):
        return f"{self.truong_du_lieu.name}: {self.value}"


class GiaiNgan(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Tên giải ngân'))
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Số tiền'))
    date = models.DateField(verbose_name=_('Ngày giải ngân'))
    ho_so_cong_viec = models.ForeignKey(HoSoCongViec, on_delete=models.CASCADE, related_name='giai_ngan', verbose_name=_('Hồ sơ công việc'))

    def __str__(self):
        return self.name


class GoiThau(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Tên gói thầu'))
    description = models.TextField(blank=True, verbose_name=_('Mô tả'))
    ho_so_cong_viec = models.ForeignKey(HoSoCongViec, on_delete=models.CASCADE, related_name='goi_thau', verbose_name=_('Hồ sơ công việc'))

    def __str__(self):
        return self.name
