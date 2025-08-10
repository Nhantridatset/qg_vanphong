from django.http import JsonResponse, FileResponse, HttpResponse # Dùng để trả về file Excel
import io # Dùng để làm việc với file trong bộ nhớ
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages # Để hiển thị thông báo cho người dùng
from django.contrib.auth.decorators import login_required # Dành cho function-based views
from django.contrib.auth.mixins import LoginRequiredMixin # Dành cho class-based views
from django.views.generic import ListView
from django.http import JsonResponse, FileResponse, HttpResponse
import io
import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
from django.utils.translation import gettext_lazy as _

from .models import (
    CoQuan, PhongBan, HoSoCongViec, KeHoach, MocThoiGian, NhiemVu,
    TepDinhKem, LichSuCongViec, CustomReport, Notification
)
# Assuming forms exist in core/forms.py
from .forms import (
    CoQuanForm, PhongBanForm, HoSoCongViecForm, KeHoachForm, MocThoiGianForm,
    NhiemVuForm, TepDinhKemForm, LichSuCongViecForm, CustomReportForm, TaskHandoverForm
)


def home(request):
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def nhiemvu_kanban_view(request):
    context = {}
    return render(request, 'core/nhiemvu_kanban.html', context)

@login_required
def nhiemvu_calendar_view(request):
    context = {}
    return render(request, 'core/nhiemvu_calendar.html', context)

@login_required
def nhiemvu_calendar_data(request):
    events = []
    return JsonResponse(events, safe=False)

@login_required
def nhiemvu_gantt_view(request):
    context = {}
    return render(request, 'core/nhiemvu_gantt.html', context)

@login_required
def nhiemvu_gantt_data(request):
    data = []
    return JsonResponse({'data': data})

@login_required
def report_project_progress_view(request):
    return render(request, 'core/report_project_progress.html', {})

@login_required
def export_project_progress_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(inch, 10.5 * inch, "Báo cáo tiến độ dự án")
    p.line(inch, 10.4 * inch, 7.5 * inch, 10.4 * inch)
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='bao_cao_tien_do.pdf')

@login_required
def export_project_progress_excel(request):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Báo cáo tiến độ'
    headers = ['Tên dự án', 'Tiến độ (%)', 'Tổng số nhiệm vụ', 'Nhiệm vụ hoàn thành']
    for col_num, header_title in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = header_title
        cell.font = Font(bold=True)
        column_letter = get_column_letter(col_num)
        worksheet.column_dimensions[column_letter].autosize = True
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=bao_cao_tien_do.xlsx'
    workbook.save(response)
    return response

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    context = {
        'notifications': notifications
    }
    return render(request, 'core/notification_list.html', context)

@login_required
def mark_notification_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    return redirect('notification-list')

@login_required
def get_unread_notifications_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})

@require_POST
@login_required
def update_task_date_from_calendar(request):
    try:
        data = json.loads(request.body)
        task_id = data.get('id')
        new_start_str = data.get('start')
        new_end_str = data.get('end')
        if not all([task_id, new_start_str, new_end_str]):
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đủ.'}, status=400)
        task = get_object_or_404(NhiemVu, pk=task_id)
        # Add permission check here if necessary
        task.ngay_bat_dau = datetime.fromisoformat(new_start_str)
        task.ngay_ket_thuc = datetime.fromisoformat(new_end_str)
        task.save()
        return JsonResponse({'status': 'success', 'message': 'Cập nhật thành công!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def task_handover_view(request):
    if request.method == 'POST':
        form = TaskHandoverForm(request.user, request.POST)
        if form.is_valid():
            task = form.cleaned_data['task']
            new_user = form.cleaned_data['new_user']
            task.nguoi_thuc_hien = new_user
            task.save()
            messages.success(request, f"Đã bàn giao nhiệm vụ '{task.ten_nhiem_vu}' cho {new_user.username} thành công!")
            return redirect('nhiemvu-list')
    else:
        form = TaskHandoverForm(user=request.user)
    context = {'form': form}
    return render(request, 'core/task_handover.html', context)

@login_required
def approve_hosocongviec_view(request, pk):
    hosocongviec = get_object_or_404(HoSoCongViec, pk=pk)
    if request.method == 'POST':
        hosocongviec.trang_thai = HoSoCongViec.TrangThai.DA_DUYET
        hosocongviec.save()
        messages.success(request, _(f'Hồ sơ công việc "{hosocongviec.ten_ho_so_cong_viec}" đã được phê duyệt.'))
    return redirect('hosocongviec-list')

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.method == 'POST':
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, _(f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được phê duyệt.'))
    return redirect('kehoach-list')

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.method == 'POST':
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, _(f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được phê duyệt.'))
    return redirect('nhiemvu-list')

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.method == 'POST':
        rating = request.POST.get('danh_gia_sao')
        review = request.POST.get('loi_danh_gia')
        nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
        nhiemvu.danh_gia_sao = rating
        nhiemvu.loi_danh_gia = review
        nhiemvu.save()
        messages.success(request, _(f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã hoàn thành và được đánh giá.'))
    return redirect('nhiemvu-detail', pk=pk)

# --- Class-Based Views (CRUD) ---

# CoQuan Views
class CoQuanListView(LoginRequiredMixin, ListView):
    model = CoQuan
    template_name = 'core/coquan_list.html'
class CoQuanDetailView(LoginRequiredMixin, DetailView):
    model = CoQuan
    template_name = 'core/coquan_detail.html'
class CoQuanCreateView(LoginRequiredMixin, CreateView):
    model = CoQuan
    form_class = CoQuanForm
    template_name = 'core/coquan_form.html'
    success_url = reverse_lazy('coquan-list')
class CoQuanUpdateView(LoginRequiredMixin, UpdateView):
    model = CoQuan
    form_class = CoQuanForm
    template_name = 'core/coquan_form.html'
    success_url = reverse_lazy('coquan-list')
class CoQuanDeleteView(LoginRequiredMixin, DeleteView):
    model = CoQuan
    template_name = 'core/coquan_confirm_delete.html'
    success_url = reverse_lazy('coquan-list')

# PhongBan Views
class PhongBanListView(LoginRequiredMixin, ListView):
    model = PhongBan
    template_name = 'core/phongban_list.html'
class PhongBanDetailView(LoginRequiredMixin, DetailView):
    model = PhongBan
    template_name = 'core/phongban_detail.html'
class PhongBanCreateView(LoginRequiredMixin, CreateView):
    model = PhongBan
    form_class = PhongBanForm
    template_name = 'core/phongban_form.html'
    success_url = reverse_lazy('phongban-list')
class PhongBanUpdateView(LoginRequiredMixin, UpdateView):
    model = PhongBan
    form_class = PhongBanForm
    template_name = 'core/phongban_form.html'
    success_url = reverse_lazy('phongban-list')
class PhongBanDeleteView(LoginRequiredMixin, DeleteView):
    model = PhongBan
    template_name = 'core/phongban_confirm_delete.html'
    success_url = reverse_lazy('phongban-list')

# HoSoCongViec Views
class HoSoCongViecListView(LoginRequiredMixin, ListView):
    model = HoSoCongViec
    template_name = 'core/hosocongviec_list.html'
class HoSoCongViecDetailView(LoginRequiredMixin, DetailView):
    model = HoSoCongViec
    template_name = 'core/hosocongviec_detail.html'
class HoSoCongViecCreateView(LoginRequiredMixin, CreateView):
    model = HoSoCongViec
    form_class = HoSoCongViecForm
    template_name = 'core/hosocongviec_form.html'
    success_url = reverse_lazy('hosocongviec-list')
class HoSoCongViecUpdateView(LoginRequiredMixin, UpdateView):
    model = HoSoCongViec
    form_class = HoSoCongViecForm
    template_name = 'core/hosocongviec_form.html'
    success_url = reverse_lazy('hosocongviec-list')
class HoSoCongViecDeleteView(LoginRequiredMixin, DeleteView):
    model = HoSoCongViec
    template_name = 'core/hosocongviec_confirm_delete.html'
    success_url = reverse_lazy('hosocongviec-list')

# KeHoach Views
class KeHoachListView(LoginRequiredMixin, ListView):
    model = KeHoach
    template_name = 'core/kehoach_list.html'
class KeHoachDetailView(LoginRequiredMixin, DetailView):
    model = KeHoach
    template_name = 'core/kehoach_detail.html'
class KeHoachCreateView(LoginRequiredMixin, CreateView):
    model = KeHoach
    form_class = KeHoachForm
    template_name = 'core/kehoach_form.html'
    success_url = reverse_lazy('kehoach-list')
class KeHoachUpdateView(LoginRequiredMixin, UpdateView):
    model = KeHoach
    form_class = KeHoachForm
    template_name = 'core/kehoach_form.html'
    success_url = reverse_lazy('kehoach-list')
class KeHoachDeleteView(LoginRequiredMixin, DeleteView):
    model = KeHoach
    template_name = 'core/kehoach_confirm_delete.html'
    success_url = reverse_lazy('kehoach-list')

# MocThoiGian Views
class MocThoiGianListView(LoginRequiredMixin, ListView):
    model = MocThoiGian
    template_name = 'core/mocthoigian_list.html'
class MocThoiGianDetailView(LoginRequiredMixin, DetailView):
    model = MocThoiGian
    template_name = 'core/mocthoigian_detail.html'
class MocThoiGianCreateView(LoginRequiredMixin, CreateView):
    model = MocThoiGian
    form_class = MocThoiGianForm
    template_name = 'core/mocthoigian_form.html'
    success_url = reverse_lazy('mocthoigian-list')
class MocThoiGianUpdateView(LoginRequiredMixin, UpdateView):
    model = MocThoiGian
    form_class = MocThoiGianForm
    template_name = 'core/mocthoigian_form.html'
    success_url = reverse_lazy('mocthoigian-list')
class MocThoiGianDeleteView(LoginRequiredMixin, DeleteView):
    model = MocThoiGian
    template_name = 'core/mocthoigian_confirm_delete.html'
    success_url = reverse_lazy('mocthoigian-list')

# NhiemVu Views
class NhiemVuListView(LoginRequiredMixin, ListView):
    model = NhiemVu
    template_name = 'core/nhiemvu_list.html'
class NhiemVuDetailView(LoginRequiredMixin, DetailView):
    model = NhiemVu
    template_name = 'core/nhiemvu_detail.html'
class NhiemVuCreateView(LoginRequiredMixin, CreateView):
    model = NhiemVu
    form_class = NhiemVuForm
    template_name = 'core/nhiemvu_form.html'
    success_url = reverse_lazy('nhiemvu-list')
class NhiemVuUpdateView(LoginRequiredMixin, UpdateView):
    model = NhiemVu
    form_class = NhiemVuForm
    template_name = 'core/nhiemvu_form.html'
    success_url = reverse_lazy('nhiemvu-list')
class NhiemVuDeleteView(LoginRequiredMixin, DeleteView):
    model = NhiemVu
    template_name = 'core/nhiemvu_confirm_delete.html'
    success_url = reverse_lazy('nhiemvu-list')

# TepDinhKem Views
class TepDinhKemListView(LoginRequiredMixin, ListView):
    model = TepDinhKem
    template_name = 'core/tepdinhkem_list.html'
class TepDinhKemDetailView(LoginRequiredMixin, DetailView):
    model = TepDinhKem
    template_name = 'core/tepdinhkem_detail.html'
class TepDinhKemCreateView(LoginRequiredMixin, CreateView):
    model = TepDinhKem
    form_class = TepDinhKemForm
    template_name = 'core/tepdinhkem_form.html'
    success_url = reverse_lazy('tepdinhkem-list')
class TepDinhKemUpdateView(LoginRequiredMixin, UpdateView):
    model = TepDinhKem
    form_class = TepDinhKemForm
    template_name = 'core/tepdinhkem_form.html'
    success_url = reverse_lazy('tepdinhkem-list')
class TepDinhKemDeleteView(LoginRequiredMixin, DeleteView):
    model = TepDinhKem
    template_name = 'core/tepdinhkem_confirm_delete.html'
    success_url = reverse_lazy('tepdinhkem-list')

# LichSuCongViec Views
class LichSuCongViecListView(LoginRequiredMixin, ListView):
    model = LichSuCongViec
    template_name = 'core/lichsucongviec_list.html'
class LichSuCongViecDetailView(LoginRequiredMixin, DetailView):
    model = LichSuCongViec
    template_name = 'core/lichsucongviec_detail.html'
class LichSuCongViecCreateView(LoginRequiredMixin, CreateView):
    model = LichSuCongViec
    form_class = LichSuCongViecForm
    template_name = 'core/lichsucongviec_form.html'
    success_url = reverse_lazy('lichsucongviec-list')
class LichSuCongViecUpdateView(LoginRequiredMixin, UpdateView):
    model = LichSuCongViec
    form_class = LichSuCongViecForm
    template_name = 'core/lichsucongviec_form.html'
    success_url = reverse_lazy('lichsucongviec-list')
class LichSuCongViecDeleteView(LoginRequiredMixin, DeleteView):
    model = LichSuCongViec
    template_name = 'core/lichsucongviec_confirm_delete.html'
    success_url = reverse_lazy('lichsucongviec-list')

# CustomReport Views
class CustomReportListView(LoginRequiredMixin, ListView):
    model = CustomReport
    template_name = 'core/customreport_list.html'
class CustomReportDetailView(LoginRequiredMixin, DetailView):
    model = CustomReport
    template_name = 'core/customreport_detail.html'
class CustomReportCreateView(LoginRequiredMixin, CreateView):
    model = CustomReport
    form_class = CustomReportForm
    template_name = 'core/customreport_form.html'
    success_url = reverse_lazy('customreport-list')
class CustomReportUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomReport
    form_class = CustomReportForm
    template_name = 'core/customreport_form.html'
    success_url = reverse_lazy('customreport-list')
class CustomReportDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomReport
    template_name = 'core/customreport_confirm_delete.html'
    success_url = reverse_lazy('customreport-list')

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font

def home(request):
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def nhiemvu_kanban_view(request):
    """
    View này sẽ xử lý logic và hiển thị Kanban board cho các nhiệm vụ.
    """
    # Ví dụ: Lấy danh sách các nhiệm vụ từ database để hiển thị
    # tasks = Task.objects.all() 
    context = {
        # 'tasks': tasks,
    }
    # Giả sử bạn có template tại core/templates/nhiemvu/kanban.html
    return render(request, 'nhiemvu/kanban.html', context)

@login_required
def nhiemvu_calendar_view(request):
    """
    View này sẽ xử lý logic và hiển thị Lịch nhiệm vụ.
    """
    # Viết logic để lấy dữ liệu cho calendar ở đây
    context = {}
    # Giả sử bạn có template tại core/templates/nhiemvu/calendar.html
    return render(request, 'nhiemvu/calendar.html', context)

#  THÊM FUNCTION MỚI ĐỂ CUNG CẤP DATA CHO CALENDAR
@login_required
def nhiemvu_calendar_data(request):
    """
    Cung cấp dữ liệu các sự kiện (nhiệm vụ) cho calendar dưới dạng JSON.
    """
    # Ví dụ: Lấy tất cả nhiệm vụ của người dùng hiện tại
    # tasks = NhiemVu.objects.filter(user=request.user)
    
    # Chuyển đổi dữ liệu thành list các dictionary mà thư viện calendar (như FullCalendar) có thể hiểu
    events = []
    # for task in tasks:
    #     events.append({
    #         'title': task.ten_nhiem_vu,
    #         'start': task.ngay_bat_dau.isoformat(), # Dùng isoformat() để có chuỗi ngày tháng chuẩn
    #         'end': task.ngay_ket_thuc.isoformat(),
    #         'id': task.id, # Gửi kèm ID để xử lý sự kiện click/update
    #         # 'url': task.get_absolute_url(), # Hoặc có thể là URL để xem chi tiết
    #     })

    # Trả về một JsonResponse. `safe=False` là cần thiết khi trả về một list.
    return JsonResponse(events, safe=False)

@login_required
def nhiemvu_gantt_view(request):
    """
    View này sẽ xử lý logic và hiển thị biểu đồ Gantt cho các nhiệm vụ.
    """
    context = {}
    # Giả sử bạn có template tại core/templates/nhiemvu/gantt.html
    return render(request, 'nhiemvu/gantt.html', context)

#  THÊM FUNCTION NÀY VÀO
@login_required
def nhiemvu_gantt_data(request):
    """
    Cung cấp dữ liệu cho biểu đồ Gantt dưới dạng JSON.
    """
    # tasks = NhiemVu.objects.all() # Lấy dữ liệu từ model
    data = []
    # for task in tasks:
    #     data.append({
    #         'id': task.id,
    #         'text': task.ten_nhiem_vu,
    #         'start_date': task.ngay_bat_dau.strftime('%Y-%m-%d'), # Định dạng Y-m-d
    #         'duration': (task.ngay_ket_thuc - task.ngay_bat_dau).days, # Tính số ngày
    #         'progress': task.progress, # ví dụ: 0.6
    #         'open': True,
    #     })

    # Trả về JSON theo định dạng mà nhiều thư viện Gantt mong muốn
    return JsonResponse({'data': data})

@login_required
def report_project_progress_view(request):
    """
    View này xử lý logic và hiển thị trang báo cáo tiến độ dự án.
    """
    # --- Logic xử lý dữ liệu báo cáo (đây là ví dụ) ---
    # 1. Lấy danh sách các dự án
    # projects = DuAn.objects.all()
    #
    # 2. Với mỗi dự án, tính toán tiến độ
    # report_data = []
    # for project in projects:
    #     total_tasks = NhiemVu.objects.filter(du_an=project).count()
    #     completed_tasks = NhiemVu.objects.filter(du_an=project, trang_thai='hoan_thanh').count()
    #     progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    #     report_data.append({
    #         'ten_du_an': project.ten_du_an,
    #         'progress': round(progress, 2),
    #         'total_tasks': total_tasks,
    #         'completed_tasks': completed_tasks,
    #     })
    #
    # context = {
    #     'report_data': report_data
    # }
    
    # Render ra template, ban đầu có thể truyền context rỗng
    return render(request, 'reports/project_progress.html', {}) # Truyền context vào đây khi đã có dữ liệu

#  THÊM FUNCTION MỚI ĐỂ XUẤT PDF
@login_required
def export_project_progress_pdf(request):
    # 1. Tạo một file-like buffer để nhận dữ liệu PDF.
    buffer = io.BytesIO()

    # 2. Tạo file PDF, sử dụng buffer làm "file" của nó.
    p = canvas.Canvas(buffer)

    # 3. Vẽ nội dung lên PDF.
    # Đây là ví dụ đơn giản, bạn có thể vẽ bảng, biểu đồ phức tạp hơn.
    p.drawString(inch, 10.5 * inch, "Báo cáo tiến độ dự án")
    p.line(inch, 10.4 * inch, 7.5 * inch, 10.4 * inch) # Vẽ đường kẻ ngang

    # Lấy dữ liệu tương tự như view báo cáo
    # report_data = [...] 
    
    y_position = 10 * inch
    # for item in report_data:
    #     text = f"Dự án: {item['ten_du_an']} - Tiến độ: {item['progress']}%"
    #     p.drawString(inch, y_position, text)
    #     y_position -= 0.3 * inch # Di chuyển xuống dòng tiếp theo
    #     if y_position < inch: # Sang trang mới nếu hết chỗ
    #         p.showPage()
    #         y_position = 10.5 * inch
    
    # 4. Đóng file PDF.
    p.showPage()
    p.save()

    # 5. Đưa con trỏ buffer về đầu file, sẵn sàng để đọc.
    buffer.seek(0)

    # 6. Trả về FileResponse để trình duyệt tải file xuống.
    # 'as_attachment=True' sẽ hiện hộp thoại "Save As...".
    return FileResponse(buffer, as_attachment=True, filename='bao_cao_tien_do.pdf')

#  THÊM FUNCTION MỚI ĐỂ XUẤT EXCEL
@login_required
def export_project_progress_excel(request):
    # 1. Lấy dữ liệu báo cáo (tương tự các view trước)
    # report_data = [...] 

    # 2. Tạo một workbook và worksheet mới
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Báo cáo tiến độ'

    # 3. Viết header cho bảng
    headers = ['Tên dự án', 'Tiến độ (%)', 'Tổng số nhiệm vụ', 'Nhiệm vụ hoàn thành']
    for col_num, header_title in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = header_title
        # In đậm header cho đẹp
        cell.font = Font(bold=True)
        # Tự động điều chỉnh độ rộng cột
        column_letter = get_column_letter(col_num)
        worksheet.column_dimensions[column_letter].autosize = True

    # 4. Viết dữ liệu vào các dòng (bắt đầu từ dòng thứ 2)
    # for row_num, item in enumerate(report_data, 2): 
    #     worksheet.cell(row=row_num, column=1).value = item['ten_du_an']
    #     worksheet.cell(row=row_num, column=2).value = item['progress']
    #     worksheet.cell(row=row_num, column=3).value = item['total_tasks']
    #     worksheet.cell(row=row_num, column=4).value = item['completed_tasks']

    # 5. Tạo response để trả về file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=bao_cao_tien_do.xlsx'
    
    # 6. Lưu workbook vào response
    workbook.save(response)

    return response

@login_required
def notification_list(request):
    """
    View này xử lý logic và hiển thị danh sách thông báo.
    """
    context = {}
    # Giả sử bạn có template tại core/templates/core/notification_list.html
    return render(request, 'core/notification_list.html', context)

#  THÊM FUNCTION MỚI ĐỂ ĐÁNH DẤU ĐÃ ĐỌC
@login_required
def mark_notification_as_read(request, pk):
    """
    Đánh dấu một thông báo cụ thể là đã đọc và chuyển hướng người dùng
    về lại trang danh sách thông báo.
    """
    # 1. Lấy đối tượng thông báo dựa vào primary key (pk).
    # Đảm bảo rằng chỉ chủ sở hữu của thông báo mới có thể đánh dấu nó.
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    # 2. Cập nhật trạng thái nếu nó chưa được đọc
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    # 3. Chuyển hướng người dùng về trang danh sách thông báo
    # Hoặc bạn có thể chuyển hướng đến URL mà thông báo đó trỏ tới (ví dụ: chi tiết nhiệm vụ)
    return redirect('notification-list') # Sử dụng name của URL để redirect

#  THÊM FUNCTION MỚI ĐỂ ĐẾM SỐ THÔNG BÁO CHƯA ĐỌC
@login_required
def get_unread_notifications_count(request):
    """
    API endpoint này trả về số lượng thông báo chưa đọc của người dùng hiện tại.
    Thường được gọi bằng JavaScript (AJAX/Fetch) để cập nhật con số trên giao diện.
    """
    # 1. Đếm số thông báo chưa đọc của người dùng hiện tại
    # count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # 2. Trả về dưới dạng JSON
    # return JsonResponse({'unread_count': count})
    
    # Tạm thời trả về 0 để server chạy được
    return JsonResponse({'unread_count': 0})

#  THÊM FUNCTION MỚI ĐỂ CẬP NHẬT NGÀY TỪ CALENDAR
# @csrf_exempt # Cảnh báo: Chỉ dùng để test. Trong production, bạn nên gửi CSRF token với AJAX.
@require_POST # Endpoint này chỉ nên nhận request POST
@login_required
def update_task_date_from_calendar(request):
    """
    API endpoint để cập nhật ngày bắt đầu/kết thúc của một nhiệm vụ
    khi người dùng kéo-thả trên calendar.
    """
    try:
        # 1. Đọc dữ liệu JSON từ body của request
        data = json.loads(request.body)
        task_id = data.get('id')
        new_start_str = data.get('start')
        new_end_str = data.get('end')

        if not all([task_id, new_start_str, new_end_str]):
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đủ.'}, status=400)

        # 2. Lấy object NhiemVu và đảm bảo user có quyền
        # task = get_object_or_404(NhiemVu, pk=task_id, du_an__thanh_vien=request.user) # Ví dụ kiểm tra quyền

        # 3. Chuyển đổi chuỗi ngày tháng thành object datetime
        # Định dạng có thể thay đổi tùy vào thư viện calendar bạn dùng.
        # Ví dụ: '2025-08-10T00:00:00'
        # task.ngay_bat_dau = datetime.fromisoformat(new_start_str)
        # task.ngay_ket_thuc = datetime.fromisoformat(new_end_str)
        
        # 4. Lưu lại thay đổi
        # task.save()

        # 5. Trả về thông báo thành công
        return JsonResponse({'status': 'success', 'message': 'Cập nhật thành công!'})

    except Exception as e:
        # Ghi lại lỗi để debug
        # print(e)
        return JsonResponse({'status': 'error', 'message': 'Có lỗi xảy ra phía server.'}, status=500)

#  THÊM FUNCTION MỚI CHO CHỨC NĂNG BÀN GIAO NHIỆM VỤ
@login_required
def task_handover_view(request):
    """
    View để xử lý việc bàn giao nhiệm vụ từ người này sang người khác.
    """
    # if request.method == 'POST':
    #     form = TaskHandoverForm(request.user, request.POST) # Truyền request.user vào form
    #     if form.is_valid():
    #         task = form.cleaned_data['task']
    #         new_user = form.cleaned_data['new_user']
    #
    #         # Kiểm tra quyền: người dùng hiện tại có phải là người đang thực hiện không
    #         # (bước này đã được xử lý trong form, nhưng kiểm tra lại vẫn tốt)
    #         if task.nguoi_thuc_hien == request.user:
    #             original_user = task.nguoi_thuc_hien
    #             task.nguoi_thuc_hien = new_user
    #             task.save()
    #
    #             # (Tùy chọn) Tạo một thông báo hoặc ghi lại lịch sử thay đổi
    #             # ...
    #
    #             messages.success(request, f"Đã bàn giao nhiệm vụ '{task.ten_nhiem_vu}' cho {new_user.username} thành công!")
    #             return redirect('some-task-list-view') # Chuyển hướng về trang danh sách nhiệm vụ
    # else:
    #     # Truyền request.user vào để form biết cần lấy nhiệm vụ của ai
    #     form = TaskHandoverForm(user=request.user)

    # context = {'form': form}
    return render(request, 'tasks/handover.html', {}) # Truyền context vào

#  THÊM FUNCTION MỚI CHO CHỨC NĂNG BÀN GIAO NHIỆM VỤ
@login_required
def task_handover_view(request):
    """
    View để xử lý việc bàn giao nhiệm vụ từ người này sang người khác.
    """
    # if request.method == 'POST':
    #     form = TaskHandoverForm(request.user, request.POST) # Truyền request.user vào form
    #     if form.is_valid():
    #         task = form.cleaned_data['task']
    #         new_user = form.cleaned_data['new_user']
    #
    #         # Kiểm tra quyền: người dùng hiện tại có phải là người đang thực hiện không
    #         # (bước này đã được xử lý trong form, nhưng kiểm tra lại vẫn tốt)
    #         if task.nguoi_thuc_hien == request.user:
    #             original_user = task.nguoi_thuc_hien
    #             task.nguoi_thuc_hien = new_user
    #             task.save()
    #
    #             # (Tùy chọn) Tạo một thông báo hoặc ghi lại lịch sử thay đổi
    #             # ...
    #
    #             messages.success(request, f"Đã bàn giao nhiệm vụ '{task.ten_nhiem_vu}' cho {new_user.username} thành công!")
    #             return redirect('some-task-list-view') # Chuyển hướng về trang danh sách nhiệm vụ
    # else:
    #     # Truyền request.user vào để form biết cần lấy nhiệm vụ của ai
    #     form = TaskHandoverForm(user=request.user)

    # context = {'form': form}
    return render(request, 'tasks/handover.html', {}) # Truyền context vào

@login_required
def approve_hosocongviec_view(request, pk):
    hosocongviec = get_object_or_404(HoSoCongViec, pk=pk)
    if request.method == 'POST':
        hosocongviec.trang_thai = HoSoCongViec.TrangThai.DA_DUYET
        hosocongviec.save()
        messages.success(request, _(f'Hồ sơ công việc "{hosocongviec.ten_ho_so_cong_viec}" đã được phê duyệt.'))
    return redirect('hosocongviec-list')

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.method == 'POST':
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, _(f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được phê duyệt.'))
    return redirect('kehoach-list')

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.method == 'POST':
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, _(f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được phê duyệt.'))
    return redirect('nhiemvu-list')

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.method == 'POST':
        rating = request.POST.get('danh_gia_sao')
        review = request.POST.get('loi_danh_gia')
        
        nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
        nhiemvu.danh_gia_sao = rating
        nhiemvu.loi_danh_gia = review
        nhiemvu.save()
        messages.success(request, _(f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã hoàn thành và được đánh giá.'))
    return redirect('nhiemvu-detail', pk=pk)