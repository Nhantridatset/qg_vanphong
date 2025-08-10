from django import forms
import json
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

class KeHoachForm(forms.ModelForm):
    class Meta:
        model = KeHoach
        fields = '__all__'
        widgets = {
            'thoi_gian_bat_dau': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'thoi_gian_ket_thuc': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

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
        fields = '__all__'
        widgets = {
            'ngay_bat_dau': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ngay_ket_thuc': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'thoi_gian_uoc_tinh': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
            'thoi_gian_thuc_te': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
            'recurring_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

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
        fields = '__all__'

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
