from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('nhiemvu/kanban/', views.nhiemvu_kanban_view, name='nhiemvu-kanban'),
    path('nhiemvu/calendar/', views.nhiemvu_calendar_view, name='nhiemvu-calendar'),
    path('nhiemvu/calendar/data/', views.nhiemvu_calendar_data, name='nhiemvu-calendar-data'),
    path('nhiemvu/gantt/', views.nhiemvu_gantt_view, name='nhiemvu-gantt'),
    path('nhiemvu/gantt/data/', views.nhiemvu_gantt_data, name='nhiemvu-gantt-data'),

    # Report URLs
    path('reports/project-progress/', views.report_project_progress_view, name='report-project-progress'),
    path('reports/project-progress/pdf/', views.export_project_progress_pdf, name='export-project-progress-pdf'),
    path('reports/project-progress/excel/', views.export_project_progress_excel, name='export-project-progress-excel'),

    # Notification URLs
    path('notifications/', views.notification_list, name='notification-list'),
    path('notifications/mark-as-read/<int:pk>/', views.mark_notification_as_read, name='mark-notification-as-read'),
    path('notifications/unread_count/', views.get_unread_notifications_count, name='unread-notifications-count'),
    path('nhiemvu/update-date/', views.update_task_date_from_calendar, name='update-task-date-from-calendar'),

    # Task Handover URL
    path('tasks/handover/', views.task_handover_view, name='task-handover'),

    # HoSoCongViec URLs
    path('hosocongviec/', views.HoSoCongViecListView.as_view(), name='hosocongviec-list'),
    path('hosocongviec/<int:pk>/', views.HoSoCongViecDetailView.as_view(), name='hosocongviec-detail'),
    path('hosocongviec/new/', views.HoSoCongViecCreateView.as_view(), name='hosocongviec-create'),
    path('hosocongviec/<int:pk>/edit/', views.HoSoCongViecUpdateView.as_view(), name='hosocongviec-update'),
    path('hosocongviec/<int:pk>/delete/', views.HoSoCongViecDeleteView.as_view(), name='hosocongviec-delete'),

    # KeHoach URLs
    path('kehoach/', views.KeHoachListView.as_view(), name='kehoach-list'),
    path('kehoach/<int:pk>/', views.KeHoachDetailView.as_view(), name='kehoach-detail'),
    path('kehoach/new/', views.KeHoachCreateView.as_view(), name='kehoach-create'),
    path('kehoach/<int:pk>/edit/', views.KeHoachUpdateView.as_view(), name='kehoach-update'),
    path('kehoach/<int:pk>/delete/', views.KeHoachDeleteView.as_view(), name='kehoach-delete'),

    # MocThoiGian URLs
    path('mocthoigian/', views.MocThoiGianListView.as_view(), name='mocthoigian-list'),
    path('mocthoigian/<int:pk>/', views.MocThoiGianDetailView.as_view(), name='mocthoigian-detail'),
    path('mocthoigian/new/', views.MocThoiGianCreateView.as_view(), name='mocthoigian-create'),
    path('mocthoigian/<int:pk>/edit/', views.MocThoiGianUpdateView.as_view(), name='mocthoigian-update'),
    path('mocthoigian/<int:pk>/delete/', views.MocThoiGianDeleteView.as_view(), name='mocthoigian-delete'),

    # NhiemVu URLs
    path('nhiemvu/', views.NhiemVuListView.as_view(), name='nhiemvu-list'),
    path('nhiemvu/<int:pk>/', views.NhiemVuDetailView.as_view(), name='nhiemvu-detail'),
    path('nhiemvu/new/', views.NhiemVuCreateView.as_view(), name='nhiemvu-create'),
    path('nhiemvu/<int:pk>/edit/', views.NhiemVuUpdateView.as_view(), name='nhiemvu-update'),
    path('nhiemvu/<int:pk>/delete/', views.NhiemVuDeleteView.as_view(), name='nhiemvu-delete'),

    # CoQuan URLs
    path('coquan/', views.CoQuanListView.as_view(), name='coquan-list'),
    path('coquan/<int:pk>/', views.CoQuanDetailView.as_view(), name='coquan-detail'),
    path('coquan/new/', views.CoQuanCreateView.as_view(), name='coquan-create'),
    path('coquan/<int:pk>/edit/', views.CoQuanUpdateView.as_view(), name='coquan-update'),
    path('coquan/<int:pk>/delete/', views.CoQuanDeleteView.as_view(), name='coquan-delete'),

    # PhongBan URLs
    path('phongban/', views.PhongBanListView.as_view(), name='phongban-list'),
    path('phongban/<int:pk>/', views.PhongBanDetailView.as_view(), name='phongban-detail'),
    path('phongban/new/', views.PhongBanCreateView.as_view(), name='phongban-create'),
    path('phongban/<int:pk>/edit/', views.PhongBanUpdateView.as_view(), name='phongban-update'),
    path('phongban/<int:pk>/delete/', views.PhongBanDeleteView.as_view(), name='phongban-delete'),

    # TepDinhKem URLs
    path('tepdinhkem/', views.TepDinhKemListView.as_view(), name='tepdinhkem-list'),
    path('tepdinhkem/<int:pk>/', views.TepDinhKemDetailView.as_view(), name='tepdinhkem-detail'),
    path('tepdinhkem/new/', views.TepDinhKemCreateView.as_view(), name='tepdinhkem-create'),
    path('tepdinhkem/<int:pk>/edit/', views.TepDinhKemUpdateView.as_view(), name='tepdinhkem-update'),
    path('tepdinhkem/<int:pk>/delete/', views.TepDinhKemDeleteView.as_view(), name='tepdinhkem-delete'),

    # LichSuCongViec URLs
    path('lichsucongviec/', views.LichSuCongViecListView.as_view(), name='lichsucongviec-list'),
    path('lichsucongviec/<int:pk>/', views.LichSuCongViecDetailView.as_view(), name='lichsucongviec-detail'),
    path('lichsucongviec/new/', views.LichSuCongViecCreateView.as_view(), name='lichsucongviec-create'),
    path('lichsucongviec/<int:pk>/edit/', views.LichSuCongViecUpdateView.as_view(), name='lichsucongviec-update'),
    path('lichsucongviec/<int:pk>/delete/', views.LichSuCongViecDeleteView.as_view(), name='lichsucongviec-delete'),

    # CustomReport URLs
    path('custom-reports/', views.CustomReportListView.as_view(), name='customreport-list'),
    path('custom-reports/new/', views.CustomReportCreateView.as_view(), name='customreport-create'),
    path('custom-reports/<int:pk>/', views.CustomReportDetailView.as_view(), name='customreport-detail'),
    path('custom-reports/<int:pk>/edit/', views.CustomReportUpdateView.as_view(), name='customreport-update'),
    path('custom-reports/<int:pk>/delete/', views.CustomReportDeleteView.as_view(), name='customreport-delete'),

    # Approval URLs
    path('hosocongviec/<int:pk>/approve/', views.approve_hosocongviec_view, name='approve-hosocongviec'),
    path('kehoach/<int:pk>/approve/', views.approve_kehoach_view, name='approve-kehoach'),
    path('nhiemvu/<int:pk>/approve/', views.approve_nhiemvu_view, name='approve-nhiemvu'),

    # Completion and Rating URL
    path('nhiemvu/<int:pk>/complete-and-rate/', views.complete_and_rate_nhiemvu_view, name='complete-and-rate-nhiemvu'),
]