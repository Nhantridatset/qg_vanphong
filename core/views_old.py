from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import HoSoCongViec, KeHoach, MocThoiGian, NhiemVu, CoQuan, PhongBan, TepDinhKem, LichSuCongViec, Notification, BinhLuan, CustomReport
from .forms import DuAnForm, KeHoachForm, MocThoiGianForm, NhiemVuForm, CoQuanForm, PhongBanForm, TepDinhKemForm, LichSuCongViecForm, TaskHandoverForm, BinhLuanForm, CustomReportForm
from django.db.models import Q
from users.models import CustomUser
from itertools import groupby
from django.http import JsonResponse, HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from openpyxl import Workbook
from django.contrib import messages
import json
from datetime import datetime

def home(request):
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'assigned_tasks': None,
        'department_tasks': None,
        'agency_projects': None,
        'all_projects': None,
        'all_tasks': None,
        'department_plans': None,
        'department_projects': None,
    }

    if user.role == CustomUser.Role.CHUYEN_VIEN:
        context['assigned_tasks'] = NhiemVu.objects.filter(id_nguoi_thuc_hien=user)
    elif user.role == CustomUser.Role.LANH_DAO_PHONG:
        if user.phong_ban:
            context['department_tasks'] = NhiemVu.objects.filter(id_ke_hoach__id_don_vi_thuc_hien=user.phong_ban)
            context['department_plans'] = KeHoach.objects.filter(Q(id_don_vi_thuc_hien=user.phong_ban) | Q(id_nguoi_phu_trach=user))
                        context['department_projects'] = HoSoCongViec.objects.filter(Q(id_don_vi_chu_tri=user.phong_ban) | Q(id_nguoi_quan_ly=user))
    elif user.role == CustomUser.Role.LANH_DAO_CO_QUAN:
        if user.co_quan:
            context['agency_projects'] = HoSoCongViec.objects.filter(Q(id_don_vi_chu_tri__co_quan=user.co_quan) | Q(id_nguoi_quan_ly=user))
    elif user.role == CustomUser.Role.ADMIN_TCI_CAO or user.role == CustomUser.Role.ADMIN_DON_VI:
        context['all_projects'] = HoSoCongViec.objects.all()
    elif user.role == CustomUser.Role.LANH_DAO_CO_QUAN:
        if user.co_quan:
            context['agency_projects'] = HoSoCongViec.objects.filter(Q(id_don_vi_chu_tri__co_quan=user.co_quan) | Q(id_nguoi_quan_ly=user))
    elif user.role == CustomUser.Role.ADMIN_TCI_CAO or user.role == CustomUser.Role.ADMIN_DON_VI:
        context['all_projects'] = HoSoCongViec.objects.all()
        context['all_tasks'] = NhiemVu.objects.all()

    return render(request, 'core/dashboard.html', context)

@login_required
def nhiemvu_kanban_view(request):
    tasks = NhiemVu.objects.all().order_by('trang_thai')
    tasks_by_status = {}
    for status_code, status_name in NhiemVu.TrangThai.choices:
        tasks_by_status[status_name] = []

    for task in tasks:
        tasks_by_status[task.get_trang_thai_display()].append(task)

    context = {
        'tasks_by_status': tasks_by_status,
        'task_statuses': NhiemVu.TrangThai.choices,
    }
    return render(request, 'core/nhiemvu_kanban.html', context)

@login_required
def nhiemvu_calendar_view(request):
    return render(request, 'core/nhiemvu_calendar.html')

@login_required
def nhiemvu_calendar_data(request):
    tasks = NhiemVu.objects.all()
    events = []
    for task in tasks:
        events.append({
            'title': task.ten_nhiem_vu,
            'start': task.ngay_ket_thuc.isoformat(),
            'url': reverse_lazy('nhiemvu-detail', kwargs={'pk': task.pk})
        })
    return JsonResponse(events, safe=False)

@login_required
def nhiemvu_gantt_view(request):
    return render(request, 'core/nhiemvu_gantt.html')

@login_required
def nhiemvu_gantt_data(request):
    tasks = NhiemVu.objects.all()
    gantt_tasks = []
    for task in tasks:
        # Frappe Gantt expects start and end dates. NhiemVu only has ngay_ket_thuc.
        # In a real scenario, you might want to add a 'ngay_bat_dau' field to NhiemVu.
        gantt_tasks.append({
            'id': str(task.pk),
            'name': task.ten_nhiem_vu,
            'start': task.ngay_bat_dau.strftime('%Y-%m-%d') if task.ngay_bat_dau else task.ngay_ket_thuc.strftime('%Y-%m-%d'),
            'end': task.ngay_ket_thuc.strftime('%Y-%m-%d'),
            'progress': 100 if task.trang_thai == NhiemVu.TrangThai.HOAN_THANH else 0,
            'dependencies': str(task.id_nhiem_vu_cha.pk) if task.id_nhiem_vu_cha else '',
        })
    return JsonResponse(gantt_tasks, safe=False)

@login_required
def report_project_progress_view(request):
    projects = HoSoCongViec.objects.all()
    context = {
        'projects': projects
    }
    return render(request, 'core/report_project_progress.html', context)

@login_required
def export_project_progress_pdf(request):
    projects = HoSoCongViec.objects.all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleStyleSheet()

    elements = []
    elements.append(Paragraph("Báo cáo Tiến độ Hồ sơ công việc", styles['h1']))

    data = [["Tên Hồ sơ công việc", "Mã Hồ sơ công việc", "Trạng thái", "Ngày bắt đầu", "Ngày kết thúc"]]
    for project in projects:
        data.append([
            project.ten_ho_so_cong_viec,
            project.ma_ho_so_cong_viec or "",
            project.get_trang_thai_display(),
            project.ngay_bat_dau.strftime('%Y-%m-%d'),
            project.ngay_ket_thuc.strftime('%Y-%m-%d'),
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def export_project_progress_excel(request):
    projects = HoSoCongViec.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tiến độ Hồ sơ công việc"

    headers = ["Tên Hồ sơ công việc", "Mã Hồ sơ công việc", "Trạng thái", "Ngày bắt đầu", "Ngày kết thúc"]
    ws.append(headers)

    for project in projects:
        ws.append([
            project.ten_ho_so_cong_viec,
            project.ma_ho_so_cong_viec or "",
            project.get_trang_thai_display(),
            project.ngay_bat_dau.strftime('%Y-%m-%d'),
            project.ngay_ket_thuc.strftime('%Y-%m-%d'),
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="bao_cao_tien_do_ho_so_cong_viec.xlsx"'

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'core/notification_list.html', {'notifications': notifications})

@login_required
def mark_notification_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notification-list')

@login_required
def task_handover_view(request):
    if request.method == 'POST':
        form = TaskHandoverForm(request.POST)
        if form.is_valid():
            task = form.cleaned_data['task']
            new_assignee = form.cleaned_data['new_assignee']
            
            old_assignee = task.id_nguoi_thuc_hien
            task.id_nguoi_thuc_hien = new_assignee
            task.save()

            # Create a history entry
            LichSuCongViec.objects.create(
                mo_ta=f'Bàn giao nhiệm vụ từ {old_assignee.username if old_assignee else "N/A"} sang {new_assignee.username}',
                user=request.user,
                nhiem_vu=task
            )
            # Create notifications
            Notification.objects.create(
                user=new_assignee,
                message=f'Nhiệm vụ "{task.ten_nhiem_vu}" đã được bàn giao cho bạn.',
                related_task=task
            )
            if old_assignee:
                Notification.objects.create(
                    user=old_assignee,
                    message=f'Nhiệm vụ "{task.ten_nhiem_vu}" đã được bàn giao từ bạn.',
                    related_task=task
                )

            messages.success(request, 'Nhiệm vụ đã được bàn giao thành công.')
            return redirect('dashboard') # Redirect to dashboard or task list
    else:
        form = TaskHandoverForm()
    return render(request, 'core/task_handover.html', {'form': form})

@login_required
def get_unread_notifications_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

@login_required
def nhiemvu_detail_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    binh_luan = nhiemvu.binh_luan.filter(parent__isnull=True) # Get top-level comments
    form = BinhLuanForm()

    if request.method == 'POST':
        form = BinhLuanForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.nhiem_vu = nhiemvu
            new_comment.user = request.user
            
            # Handle replies
            parent_id = request.POST.get('parent_id')
            if parent_id:
                new_comment.parent = BinhLuan.objects.get(id=parent_id)

            new_comment.save()

            # Create history and notification
            LichSuCongViec.objects.create(
                nhiem_vu=nhiemvu,
                user=request.user,
                mo_ta=f"đã thêm một bình luận mới."
            )
            # Notify task assignee (if not the one commenting)
            if nhiemvu.id_nguoi_thuc_hien != request.user:
                 Notification.objects.create(
                    user=nhiemvu.id_nguoi_thuc_hien,
                    message=f'{request.user.username} đã bình luận về nhiệm vụ "{nhiemvu.ten_nhiem_vu}".',
                    related_task=nhiemvu
                )

            return redirect('nhiemvu-detail', pk=pk)

    context = {
        'object': nhiemvu,
        'binh_luan': binh_luan,
        'form': form,
        'can_approve_task': request.user.is_authenticated and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO and request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG]
    }
    return render(request, 'core/nhiemvu_detail.html', context)


@login_required
def update_task_date_from_calendar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            new_end_date_str = data.get('new_end_date')

            task = get_object_or_404(NhiemVu, pk=task_id)
            old_end_date = task.ngay_ket_thuc

            # Convert new_end_date_str to datetime object
            # Assuming new_end_date_str is in ISO format (e.g., "2025-08-08T12:00:00Z")
            new_end_date = datetime.fromisoformat(new_end_date_str.replace('Z', '+00:00'))

            task.ngay_ket_thuc = new_end_date
            task.save()

            # Log the change
            LichSuCongViec.objects.create(
                nhiem_vu=task,
                user=request.user,
                mo_ta=f"đã cập nhật ngày kết thúc nhiệm vụ từ lịch.",
                details={'Ngày kết thúc': {'from': old_end_date.isoformat(), 'to': new_end_date.isoformat()}}
            )

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# HoSoCongViec Views
class HoSoCongViecListView(ListView):
    model = HoSoCongViec
    template_name = 'core/hosocongviec_list.html'
    context_object_name = 'hosocongviec_list'

class HoSoCongViecDetailView(DetailView):
    model = HoSoCongViec
    template_name = 'core/hosocongviec_detail.html'

class HoSoCongViecCreateView(CreateView):
    model = HoSoCongViec
    form_class = HoSoCongViecForm
    template_name = 'core/hosocongviec_form.html'
    success_url = reverse_lazy('hosocongviec-list')

class HoSoCongViecUpdateView(UpdateView):
    model = HoSoCongViec
    form_class = HoSoCongViecForm
    template_name = 'core/hosocongviec_form.html'
    success_url = reverse_lazy('hosocongviec-list')

class HoSoCongViecDeleteView(DeleteView):
    model = HoSoCongViec
    template_name = 'core/hosocongviec_confirm_delete.html'
    success_url = reverse_lazy('hosocongviec-list')

# KeHoach Views
class KeHoachListView(ListView):
    model = KeHoach
    template_name = 'core/kehoach_list.html'
    context_object_name = 'kehoach_list'

class KeHoachDetailView(DetailView):
    model = KeHoach
    template_name = 'core/kehoach_detail.html'

class KeHoachCreateView(CreateView):
    model = KeHoach
    form_class = KeHoachForm
    template_name = 'core/kehoach_form.html'
    success_url = reverse_lazy('kehoach-list')

class KeHoachUpdateView(UpdateView):
    model = KeHoach
    form_class = KeHoachForm
    template_name = 'core/kehoach_form.html'
    success_url = reverse_lazy('kehoach-list')

class KeHoachDeleteView(DeleteView):
    model = KeHoach
    template_name = 'core/kehoach_confirm_delete.html'
    success_url = reverse_lazy('kehoach-list')

# MocThoiGian Views
class MocThoiGianListView(ListView):
    model = MocThoiGian
    template_name = 'core/mocthoigian_list.html'
    context_object_name = 'mocthoigian_list'

class MocThoiGianDetailView(DetailView):
    model = MocThoiGian
    template_name = 'core/mocthoigian_detail.html'

class MocThoiGianCreateView(CreateView):
    model = MocThoiGian
    form_class = MocThoiGianForm
    template_name = 'core/mocthoigian_form.html'
    success_url = reverse_lazy('mocthoigian-list')

class MocThoiGianUpdateView(UpdateView):
    model = MocThoiGian
    form_class = MocThoiGianForm
    template_name = 'core/mocthoigian_form.html'
    success_url = reverse_lazy('mocthoigian-list')

class MocThoiGianDeleteView(DeleteView):
    model = MocThoiGian
    template_name = 'core/mocthoigian_confirm_delete.html'
    success_url = reverse_lazy('mocthoigian-list')

# NhiemVu Views
class NhiemVuListView(ListView):
    model = NhiemVu
    template_name = 'core/nhiemvu_list.html'
    context_object_name = 'nhiemvu_list'

class NhiemVuDetailView(DetailView):
    model = NhiemVu
    template_name = 'core/nhiemvu_detail.html'

class NhiemVuCreateView(CreateView):
    model = NhiemVu
    form_class = NhiemVuForm
    template_name = 'core/nhiemvu_form.html'
    success_url = reverse_lazy('nhiemvu-list')

class NhiemVuUpdateView(UpdateView):
    model = NhiemVu
    form_class = NhiemVuForm
    template_name = 'core/nhiemvu_form.html'
    success_url = reverse_lazy('nhiemvu-list')

class NhiemVuDeleteView(DeleteView):
    model = NhiemVu
    template_name = 'core/nhiemvu_confirm_delete.html'
    success_url = reverse_lazy('nhiemvu-list')

# CoQuan Views
class CoQuanListView(ListView):
    model = CoQuan
    template_name = 'core/coquan_list.html'
    context_object_name = 'coquan_list'

class CoQuanDetailView(DetailView):
    model = CoQuan
    template_name = 'core/coquan_detail.html'

class CoQuanCreateView(CreateView):
    model = CoQuan
    form_class = CoQuanForm
    template_name = 'core/coquan_form.html'
    success_url = reverse_lazy('coquan-list')

class CoQuanUpdateView(UpdateView):
    model = CoQuan
    form_class = CoQuanForm
    template_name = 'core/coquan_form.html'
    success_url = reverse_lazy('coquan-list')

class CoQuanDeleteView(DeleteView):
    model = CoQuan
    template_name = 'core/coquan_confirm_delete.html'
    success_url = reverse_lazy('coquan-list')

# PhongBan Views
class PhongBanListView(ListView):
    model = PhongBan
    template_name = 'core/phongban_list.html'
    context_object_name = 'phongban_list'

class PhongBanDetailView(DetailView):
    model = PhongBan
    template_name = 'core/phongban_detail.html'

class PhongBanCreateView(CreateView):
    model = PhongBan
    form_class = PhongBanForm
    template_name = 'core/phongban_form.html'
    success_url = reverse_lazy('phongban-list')

class PhongBanUpdateView(UpdateView):
    model = PhongBan
    form_class = PhongBanForm
    template_name = 'core/phongban_form.html'
    success_url = reverse_lazy('phongban-list')

class PhongBanDeleteView(DeleteView):
    model = PhongBan
    template_name = 'core/phongban_confirm_delete.html'
    success_url = reverse_lazy('phongban-list')

# TepDinhKem Views
class TepDinhKemListView(ListView):
    model = TepDinhKem
    template_name = 'core/tepdinhkem_list.html'
    context_object_name = 'tepdinhkem_list'

class TepDinhKemDetailView(DetailView):
    model = TepDinhKem
    template_name = 'core/tepdinhkem_detail.html'

class TepDinhKemCreateView(CreateView):
    model = TepDinhKem
    form_class = TepDinhKemForm
    template_name = 'core/tepdinhkem_form.html'
    success_url = reverse_lazy('tepdinhkem-list')

class TepDinhKemUpdateView(UpdateView):
    model = TepDinhKem
    form_class = TepDinhKemForm
    template_name = 'core/tepdinhkem_form.html'
    success_url = reverse_lazy('tepdinhkem-list')

class TepDinhKemDeleteView(DeleteView):
    model = TepDinhKem
    template_name = 'core/tepdinhkem_confirm_delete.html'
    success_url = reverse_lazy('tepdinhkem-list')

# LichSuCongViec Views
class LichSuCongViecListView(ListView):
    model = LichSuCongViec
    template_name = 'core/lichsucongviec_list.html'
    context_object_name = 'lichsucongviec_list'

class LichSuCongViecDetailView(DetailView):
    model = LichSuCongViec
    template_name = 'core/lichsucongviec_detail.html'

class LichSuCongViecCreateView(CreateView):
    model = LichSuCongViec
    form_class = LichSuCongViecForm
    template_name = 'core/lichsucongviec_form.html'
    success_url = reverse_lazy('lichsucongviec-list')

class LichSuCongViecUpdateView(UpdateView):
    model = LichSuCongViec
    form_class = LichSuCongViecForm
    template_name = 'core/lichsucongviec_form.html'
    success_url = reverse_lazy('lichsucongviec-list')

class LichSuCongViecDeleteView(DeleteView):
    model = LichSuCongViec
    template_name = 'core/lichsucongviec_confirm_delete.html'
    success_url = reverse_lazy('lichsucongviec-list')

# CustomReport Views
class CustomReportListView(ListView):
    model = CustomReport
    template_name = 'core/customreport_list.html'
    context_object_name = 'customreport_list'

class CustomReportCreateView(CreateView):
    model = CustomReport
    form_class = CustomReportForm
    template_name = 'core/customreport_form.html'
    success_url = reverse_lazy('customreport-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class CustomReportDetailView(DetailView):
    model = CustomReport
    template_name = 'core/customreport_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()

        # Dynamically get the model
        from django.apps import apps
        try:
            app_label = 'core' # Assuming all models are in the 'core' app for simplicity
            model = apps.get_model(app_label, report.model_name)
        except LookupError:
            context['report_data'] = []
            context['error_message'] = f"Model '{report.model_name}' not found."
            return context

        # Query data
        queryset = model.objects.all()

        # Apply user-specific filters for LANH_DAO_CO_QUAN
        if self.request.user.is_authenticated and self.request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and self.request.user.co_quan:
            user_agency = self.request.user.co_quan

            if report.model_name == 'DuAn':
                queryset = queryset.filter(Q(id_don_vi_chu_tri__co_quan=user_agency) | Q(id_nguoi_quan_ly__co_quan=user_agency))
            elif report.model_name == 'KeHoach':
                queryset = queryset.filter(Q(id_du_an__id_don_vi_chu_tri__co_quan=user_agency) | Q(id_du_an__id_nguoi_quan_ly__co_quan=user_agency))
            elif report.model_name == 'NhiemVu':
                queryset = queryset.filter(Q(id_ke_hoach__id_du_an__id_don_vi_chu_tri__co_quan=user_agency) | Q(id_ke_hoach__id_du_an__id_nguoi_quan_ly__co_quan=user_agency))
            # Add more model-specific filters here if needed for other models

        # Apply report-defined filters
        if report.filters:
            try:
                queryset = queryset.filter(**report.filters)
            except Exception as e:
                context['report_data'] = []
                context['error_message'] = f"Lỗi khi áp dụng bộ lọc: {e}"
                return context

        # Prepare data for template
        report_data = []
        for obj in queryset:
            row = {}
            for field_name in report.fields_to_display:
                try:
                    field_value = getattr(obj, field_name)
                    # Handle ForeignKey fields to display their __str__ representation
                    if hasattr(field_value, '__str__') and isinstance(obj._meta.get_field(field_name), models.ForeignKey):
                        row[field_name] = str(field_value)
                    elif isinstance(field_value, datetime):
                        row[field_name] = field_value.strftime("%d/%m/%Y %H:%M")
                    else:
                        row[field_name] = field_value
                except AttributeError:
                    row[field_name] = "N/A"
            report_data.append(row)
        
        context['report_data'] = report_data
        return context

class CustomReportUpdateView(UpdateView):
    model = CustomReport
    form_class = CustomReportForm
    template_name = 'core/customreport_form.html'
    success_url = reverse_lazy('customreport-list')

class CustomReportDeleteView(DeleteView):
    model = CustomReport
    template_name = 'core/customreport_confirm_delete.html'
    success_url = reverse_lazy('customreport-list')

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def approve_duan_view(request, pk):
    duan = get_object_or_404(DuAn, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and duan.trang_thai == DuAn.TrangThai.CHO_PHE_DUYET:
        duan.trang_thai = DuAn.TrangThai.DA_DUYET
        duan.save()
        messages.success(request, f'Dự án "{duan.ten_du_an}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt dự án {duan.ten_du_an}.",
            details={'Dự án': duan.ten_du_an, 'Trạng thái mới': duan.get_trang_thai_display()}
        )
        # Notify project manager
        if duan.id_nguoi_quan_ly:
            Notification.objects.create(
                user=duan.id_nguoi_quan_ly,
                message=f'Dự án "{duan.ten_du_an}" của bạn đã được duyệt.',
                related_project=duan
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt dự án này hoặc dự án không ở trạng thái chờ duyệt.')
    return redirect('duan-detail', pk=pk)

@login_required
def approve_kehoach_view(request, pk):
    kehoach = get_object_or_404(KeHoach, pk=pk)
    if request.user.role == CustomUser.Role.LANH_DAO_CO_QUAN and kehoach.trang_thai == KeHoach.TrangThai.CHUA_BAT_DAU:
        kehoach.trang_thai = KeHoach.TrangThai.DA_DUYET
        kehoach.save()
        messages.success(request, f'Kế hoạch "{kehoach.ten_ke_hoach}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=None, # No specific task, but related to project
            user=request.user,
            mo_ta=f"đã duyệt kế hoạch {kehoach.ten_ke_hoach}.",
            details={'Kế hoạch': kehoach.ten_ke_hoach, 'Trạng thái mới': kehoach.get_trang_thai_display()}
        )
        # Notify plan manager
        if kehoach.id_nguoi_phu_trach:
            Notification.objects.create(
                user=kehoach.id_nguoi_phu_trach,
                message=f'Kế hoạch "{kehoach.ten_ke_hoach}" của bạn đã được duyệt.',
                related_project=kehoach.id_du_an # Assuming plan is related to a project
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt kế hoạch này hoặc kế hoạch không ở trạng thái chờ duyệt.')
    return redirect('kehoach-detail', pk=pk)

@login_required
def approve_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user.role in [CustomUser.Role.LANH_DAO_CO_QUAN, CustomUser.Role.LANH_DAO_PHONG] and nhiemvu.trang_thai == NhiemVu.TrangThai.NV_CHO:
        nhiemvu.trang_thai = NhiemVu.TrangThai.DA_DUYET
        nhiemvu.save()
        messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được duyệt.')
        LichSuCongViec.objects.create(
            nhiem_vu=nhiemvu,
            user=request.user,
            mo_ta=f"đã duyệt nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
            details={'Nhiệm vụ': nhiemvu.ten_nhiem_vu, 'Trạng thái mới': nhiemvu.get_trang_thai_display()}
        )
        # Notify assignee
        if nhiemvu.id_nguoi_thuc_hien:
            Notification.objects.create(
                user=nhiemvu.id_nguoi_thuc_hien,
                message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" của bạn đã được duyệt.',
                related_task=nhiemvu
            )
    else:
        messages.error(request, 'Bạn không có quyền duyệt nhiệm vụ này hoặc nhiệm vụ không ở trạng thái chờ duyệt.')
    return redirect('nhiemvu-detail', pk=pk)

@login_required
def complete_and_rate_nhiemvu_view(request, pk):
    nhiemvu = get_object_or_404(NhiemVu, pk=pk)
    if request.user == nhiemvu.id_nguoi_thuc_hien and nhiemvu.trang_thai != NhiemVu.TrangThai.HOAN_THANH:
        if request.method == 'POST':
            danh_gia_sao = request.POST.get('danh_gia_sao')
            loi_danh_gia = request.POST.get('loi_danh_gia', '')

            if danh_gia_sao:
                nhiemvu.trang_thai = NhiemVu.TrangThai.HOAN_THANH
                nhiemvu.danh_gia_sao = int(danh_gia_sao)
                nhiemvu.loi_danh_gia = loi_danh_gia
                nhiemvu.save()
                messages.success(request, f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành và đánh giá.')
                LichSuCongViec.objects.create(
                    nhiem_vu=nhiemvu,
                    user=request.user,
                    mo_ta=f"đã hoàn thành và đánh giá nhiệm vụ {nhiemvu.ten_nhiem_vu}.",
                    details={'Trạng thái mới': nhiemvu.get_trang_thai_display(), 'Đánh giá sao': nhiemvu.danh_gia_sao, 'Lời đánh giá': nhiemvu.loi_danh_gia}
                )
                # Notify project manager/leader
                if nhiemvu.id_ke_hoach and nhiemvu.id_ke_hoach.id_nguoi_phu_trach:
                    Notification.objects.create(
                        user=nhiemvu.id_ke_hoach.id_nguoi_phu_trach,
                        message=f'Nhiệm vụ "{nhiemvu.ten_nhiem_vu}" đã được hoàn thành bởi {request.user.username}.',
                        related_task=nhiemvu
                    )
            else:
                messages.error(request, 'Vui lòng chọn số sao để đánh giá.')
        else:
            # Render a form for rating (this part will be handled in template)
            pass
    else:
        messages.error(request, 'Bạn không có quyền hoàn thành hoặc nhiệm vụ đã hoàn thành.')
    return redirect('nhiemvu-detail', pk=pk)
