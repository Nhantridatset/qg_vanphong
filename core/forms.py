from django import forms
import json
from django.db.models import Q
from django.utils import timezone
from .models import HoSoCongViec, KeHoach, MocThoiGian, NhiemVu, CoQuan, PhongBan, TepDinhKem, LichSuCongViec, BinhLuan, CustomReport, LoaiNhiemVu, TruongDuLieu, GiaTriTruongDuLieu, GiaiNgan, GoiThau
from users.models import CustomUser

class HoSoCongViecForm(forms.ModelForm):
    class Meta:
        model = HoSoCongViec
        fields = ['ten_ho_so_cong_viec', 'ma_ho_so_cong_viec', 'mo_ta', 'trang_thai', 'phan_loai_linh_vuc', 'can_cu_phap_ly', 'ngay_bat_dau', 'ngay_ket_thuc', 'id_nguoi_quan_ly', 'id_don_vi_chu_tri']
        widgets = {
            'ngay_bat_dau': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ngay_ket_thuc': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk: # Only set default for new instances
            self.initial['ngay_bat_dau'] = timezone.now()

        if self.request_user and self.request_user.phong_ban:
            # Filter id_nguoi_quan_ly to show only LANH_DAO_PHONG from the same department
            self.fields['id_nguoi_quan_ly'].queryset = CustomUser.objects.filter(
                phong_ban=self.request_user.phong_ban,
                role=CustomUser.Role.LANH_DAO_PHONG
            )

class KeHoachForm(forms.ModelForm):
    class Meta:
        model = KeHoach
        fields = '__all__'
        widgets = {
            'thoi_gian_bat_dau': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'thoi_gian_ket_thuc': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'id_don_vi_thuc_hien': forms.Select(attrs={'class': 'select2-single'}),
            'don_vi_phoi_hop': forms.SelectMultiple(attrs={'class': 'select2-multiple'}),
            'id_nguoi_phu_trach': forms.Select(attrs={'class': 'select2-single'}),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial['thoi_gian_bat_dau'] = timezone.now()

        co_quan = None
        
        # If form is bound to data (POST request), get CoQuan from submitted HoSoCongViec
        if self.is_bound:
            try:
                hscv_id = int(self.data.get('id_du_an'))
                ho_so_cong_viec = HoSoCongViec.objects.get(pk=hscv_id)
                if ho_so_cong_viec.id_don_vi_chu_tri:
                    co_quan = ho_so_cong_viec.id_don_vi_chu_tri.co_quan
            except (TypeError, ValueError, HoSoCongViec.DoesNotExist):
                pass # Keep co_quan as None
        # If form is not bound (GET request) and is for an existing instance
        elif self.instance and self.instance.pk and self.instance.id_du_an:
            if self.instance.id_du_an.id_don_vi_chu_tri:
                co_quan = self.instance.id_du_an.id_don_vi_chu_tri.co_quan
        # If form is not bound (GET request) and is for a new instance
        else:
            if self.request_user and self.request_user.co_quan:
                co_quan = self.request_user.co_quan

        # Filter the querysets if a CoQuan has been determined
        if co_quan:
            phong_ban_queryset = PhongBan.objects.filter(co_quan=co_quan)
            leader_queryset = CustomUser.objects.filter(
                co_quan=co_quan,
                role__in=[
                    CustomUser.Role.LANH_DAO_CO_QUAN,
                    CustomUser.Role.LANH_DAO_VAN_PHONG,
                    CustomUser.Role.LANH_DAO_PHONG
                ]
            )
            self.fields['id_don_vi_thuc_hien'].queryset = phong_ban_queryset
            self.fields['don_vi_phoi_hop'].queryset = phong_ban_queryset
            self.fields['id_nguoi_phu_trach'].queryset = leader_queryset
        else:
            # If no CoQuan can be determined, show no options.
            self.fields['id_don_vi_thuc_hien'].queryset = PhongBan.objects.none()
            self.fields['don_vi_phoi_hop'].queryset = PhongBan.objects.none()
            self.fields['id_nguoi_phu_trach'].queryset = CustomUser.objects.none()

class MocThoiGianForm(forms.ModelForm):
    class Meta:
        model = MocThoiGian
        fields = '__all__'
        widgets = {
            'ngay_den_han': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class NhiemVuForm(forms.ModelForm):
    class Meta:
        model = NhiemVu
        fields = [
            'ten_nhiem_vu', 'mo_ta', 'muc_do_uu_tien',
            'ngay_bat_dau', 'ngay_ket_thuc',
            'id_ke_hoach', 'id_nguoi_xu_ly_chinh', 'nguoi_dong_xu_ly', 'id_nhiem_vu_cha',
            'thoi_gian_uoc_tinh',
            'is_recurring', 'recurring_frequency', 'recurring_until',
            'id_nguoi_duyet', # New field for explicit approver
        ]
        widgets = {
            'ngay_bat_dau': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ngay_ket_thuc': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'thoi_gian_uoc_tinh': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
            'recurring_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'id_nguoi_xu_ly_chinh': forms.Select(attrs={'class': 'select2-single'}),
            'nguoi_dong_xu_ly': forms.SelectMultiple(attrs={'class': 'select2-multiple'}),
            'id_nguoi_duyet': forms.Select(attrs={'class': 'select2-single'}), # Widget for new field
        }

    def __init__(self, *args, **kwargs):
        print("DEBUG: NhiemVuForm __init__ called.")
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk: # Only set default for new instances
            self.initial['ngay_bat_dau'] = timezone.now()

        # self.fields['is_quy_trinh_dac_biet'].disabled = True # Removed as field is no longer in form

        # Filter id_nguoi_xu_ly_chinh (main assignee) based on assignment rules
        if self.request_user:
            if self.request_user.role == CustomUser.Role.LANH_DAO_CO_QUAN:
                self.fields['id_nguoi_xu_ly_chinh'].queryset = CustomUser.objects.exclude(pk=self.request_user.pk).exclude(role=CustomUser.Role.LANH_DAO_CO_QUAN)
            elif self.request_user.role == CustomUser.Role.LANH_DAO_VAN_PHONG:
                self.fields['id_nguoi_xu_ly_chinh'].queryset = CustomUser.objects.filter(
                    role__in=[
                        CustomUser.Role.LANH_DAO_PHONG,
                        CustomUser.Role.CHUYEN_VIEN_VAN_PHONG
                    ]
                ).exclude(role=CustomUser.Role.LANH_DAO_CO_QUAN)
            elif self.request_user.role == CustomUser.Role.LANH_DAO_PHONG:
                if self.request_user.phong_ban:
                    self.fields['id_nguoi_xu_ly_chinh'].queryset = CustomUser.objects.filter(
                        phong_ban=self.request_user.phong_ban,
                        role__in=[CustomUser.Role.CHUYEN_VIEN_PHONG, CustomUser.Role.LANH_DAO_PHONG]
                    ).exclude(role=CustomUser.Role.LANH_DAO_CO_QUAN)
                else:
                    self.fields['id_nguoi_xu_ly_chinh'].queryset = CustomUser.objects.none()
            elif self.request_user.role == CustomUser.Role.CHUYEN_VIEN_VAN_PHONG:
                self.fields['id_nguoi_xu_ly_chinh'].queryset = CustomUser.objects.filter(
                    Q(role=CustomUser.Role.LANH_DAO_PHONG) | Q(pk=self.request_user.pk)
                ).exclude(role=CustomUser.Role.LANH_DAO_CO_QUAN)
            elif self.request_user.role == CustomUser.Role.CHUYEN_VIEN_PHONG:
                self.fields['id_nguoi_xu_ly_chinh'].queryset = CustomUser.objects.filter(pk=self.request_user.pk).exclude(role=CustomUser.Role.LANH_DAO_CO_QUAN)
            else:
                self.fields['id_nguoi_xu_ly_chinh'].queryset = CustomUser.objects.none().exclude(role=CustomUser.Role.LANH_DAO_CO_QUAN)

            # Filter nguoi_dong_xu_ly (co-assignees) - allow all users except LANH_DAO_CO_QUAN and the main assignee
            self.fields['nguoi_dong_xu_ly'].queryset = CustomUser.objects.exclude(role=CustomUser.Role.LANH_DAO_CO_QUAN)
            if self.instance and self.instance.id_nguoi_xu_ly_chinh:
                self.fields['nguoi_dong_xu_ly'].queryset = self.fields['nguoi_dong_xu_ly'].queryset.exclude(pk=self.instance.id_nguoi_xu_ly_chinh.pk)

            # Filter id_nguoi_duyet (approver) - only LANH_DAO_CO_QUAN and LANH_DAO_VAN_PHONG
            self.fields['id_nguoi_duyet'].queryset = CustomUser.objects.filter(
                Q(role=CustomUser.Role.LANH_DAO_CO_QUAN) | Q(role=CustomUser.Role.LANH_DAO_VAN_PHONG)
            )

            # Filter id_ke_hoach (plan) based on user's role and associated projects/departments
            if self.request_user.role == CustomUser.Role.LANH_DAO_CO_QUAN:
                self.fields['id_ke_hoach'].queryset = KeHoach.objects.all()
            elif self.request_user.role == CustomUser.Role.LANH_DAO_VAN_PHONG:
                # Lanh dao Van phong sees plans related to their agency's departments
                if self.request_user.phong_ban and self.request_user.phong_ban.co_quan:
                    self.fields['id_ke_hoach'].queryset = KeHoach.objects.filter(
                        id_du_an__id_don_vi_chu_tri__co_quan=self.request_user.phong_ban.co_quan
                    )
                else:
                    self.fields['id_ke_hoach'].queryset = KeHoach.objects.none()
            elif self.request_user.role == CustomUser.Role.LANH_DAO_PHONG:
                # Lanh dao Phong sees plans related to their department
                if self.request_user.phong_ban:
                    self.fields['id_ke_hoach'].queryset = KeHoach.objects.filter(
                        id_du_an__id_don_vi_chu_tri=self.request_user.phong_ban
                    )
                else:
                    self.fields['id_ke_hoach'].queryset = KeHoach.objects.none()
            else:
                # Chuyen vien only sees plans related to tasks assigned to them or their department
                self.fields['id_ke_hoach'].queryset = KeHoach.objects.filter(
                    nhiem_vu__id_nguoi_xu_ly_chinh=self.request_user
                ).distinct() | KeHoach.objects.filter(
                    id_du_an__id_don_vi_chu_tri=self.request_user.phong_ban
                ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        assigner = self.request_user
        main_assignee = cleaned_data.get('id_nguoi_xu_ly_chinh')
        co_assignees = cleaned_data.get('nguoi_dong_xu_ly')

        if main_assignee and co_assignees and main_assignee in co_assignees:
            raise forms.ValidationError("Người xử lý chính không thể đồng thời là người đồng xử lý.")

        if assigner and main_assignee:
            is_special_workflow = (
                assigner.role == CustomUser.Role.CHUYEN_VIEN_VAN_PHONG and
                main_assignee.role == CustomUser.Role.LANH_DAO_PHONG
            )
            cleaned_data['is_quy_trinh_dac_biet'] = is_special_workflow

        return cleaned_data


class BinhLuanForm(forms.ModelForm):
    class Meta:
        model = BinhLuan
        fields = ['noi_dung']
        widgets = {
            'noi_dung': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Nhập bình luận của bạn...'}),
        }

class CoQuanForm(forms.ModelForm):
    class Meta:
        model = CoQuan
        fields = '__all__'

class PhongBanForm(forms.ModelForm):
    class Meta:
        model = PhongBan
        fields = '__all__'

class TepDinhKemForm(forms.ModelForm):
    class Meta:
        model = TepDinhKem
        fields = ['file', 'uploader', 'nhiem_vu', 'ho_so_cong_viec', 'ke_hoach', 'binh_luan']
        widgets = {
            'file': forms.FileInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nhiem_vu'].required = False
        self.fields['ho_so_cong_viec'].required = False
        self.fields['ke_hoach'].required = False
        self.fields['binh_luan'].required = False
        self.fields['uploader'].required = False # Uploader will be set in view

class LichSuCongViecForm(forms.ModelForm):
    class Meta:
        model = LichSuCongViec
        fields = '__all__'

class TaskHandoverForm(forms.Form):
    task = forms.ModelChoiceField(queryset=NhiemVu.objects.all(), label="Nhiệm vụ")
    new_assignee = forms.ModelChoiceField(queryset=CustomUser.objects.all(), label="Người nhận mới")

class CustomReportForm(forms.ModelForm):
    fields_to_display = forms.CharField(widget=forms.Textarea, help_text="Nhập danh sách các trường cần hiển thị dưới dạng JSON (ví dụ: ['ten_ho_so_cong_viec', 'trang_thai'])")
    filters = forms.CharField(required=False, widget=forms.Textarea, help_text="Nhập các bộ lọc dưới dạng JSON (ví dụ: {'trang_thai': 'HOAN_THANH'})")

    class Meta:
        model = CustomReport
        fields = ['name', 'description', 'model_name', 'fields_to_display', 'filters']

    def clean_fields_to_display(self):
        data = self.cleaned_data['fields_to_display']
        try:
            json_data = json.loads(data)
            if not isinstance(json_data, list):
                raise forms.ValidationError("Phải là một danh sách JSON hợp lệ.")
            return json_data
        except json.JSONDecodeError:
            raise forms.ValidationError("Không phải là JSON hợp lệ.")

    def clean_filters(self):
        data = self.cleaned_data['filters']
        if data:
            try:
                json_data = json.loads(data)
                if not isinstance(json_data, dict):
                    raise forms.ValidationError("Phải là một đối tượng JSON hợp lệ.")
                return json_data
            except json.JSONDecodeError:
                raise forms.ValidationError("Không phải là JSON hợp lệ.")
        return None


class LoaiNhiemVuForm(forms.ModelForm):
    class Meta:
        model = LoaiNhiemVu
        fields = '__all__'


class TruongDuLieuForm(forms.ModelForm):
    class Meta:
        model = TruongDuLieu
        fields = '__all__'


class GiaTriTruongDuLieuForm(forms.ModelForm):
    class Meta:
        model = GiaTriTruongDuLieu
        fields = '__all__'


class GiaiNganForm(forms.ModelForm):
    class Meta:
        model = GiaiNgan
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class GoiThauForm(forms.ModelForm):
    class Meta:
        model = GoiThau
        fields = '__all__'

from django.core.exceptions import ValidationError

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ExtensionRequestForm(forms.ModelForm):
    class Meta:
        model = NhiemVu
        fields = ['ngay_ket_thuc_de_xuat', 'ly_do_gia_han']
        widgets = {
            'ngay_ket_thuc_de_xuat': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class NhiemVuCompletionForm(forms.Form):
    attachments = MultipleFileField(required=False, label='Đính kèm tệp trả lời')
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label='Bình luận / Trả lời')