from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import NhiemVu, LichSuCongViec, Notification
from .middleware import get_current_user
from .utils import send_notification_email # Import the email utility

@receiver(pre_save, sender=NhiemVu)
def store_old_instance(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = NhiemVu.objects.get(pk=instance.pk)
        except NhiemVu.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None

@receiver(post_save, sender=NhiemVu)
def log_nhiemvu_changes(sender, instance, created, **kwargs):
    user = get_current_user()
    if not user or not user.is_authenticated:
        return

    if created:
        LichSuCongViec.objects.create(
            nhiem_vu=instance,
            user=user,
            mo_ta=f"đã tạo mới nhiệm vụ.",
            details={f'Tạo mới': f'{instance.ten_nhiem_vu}'}
        )
        # Notify assignee
        if instance.id_nguoi_thuc_hien and instance.id_nguoi_thuc_hien != user:
            Notification.objects.create(
                user=instance.id_nguoi_thuc_hien,
                message=f'{user.username} đã giao cho bạn nhiệm vụ mới: "{instance.ten_nhiem_vu}".',
                related_task=instance
            )
    else:
        old_instance = getattr(instance, '_old_instance', None)
        if old_instance:
            tracked_fields = {
                'ten_nhiem_vu': 'Tên nhiệm vụ',
                'mo_ta': 'Mô tả',
                'trang_thai': 'Trạng thái',
                'muc_do_uu_tien': 'Mức độ ưu tiên',
                'ngay_bat_dau': 'Ngày bắt đầu',
                'ngay_ket_thuc': 'Ngày kết thúc',
                'thoi_gian_uoc_tinh': 'Thời gian ước tính',
                'thoi_gian_thuc_te': 'Thời gian thực tế',
                'is_recurring': 'Nhiệm vụ lặp lại',
                'recurring_frequency': 'Tần suất lặp lại',
                'recurring_until': 'Lặp lại đến ngày',
                'id_nguoi_thuc_hien': 'Người thực hiện'
            }
            changes = {}
            for field, display_name in tracked_fields.items():
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    if field == 'trang_thai':
                        changes[display_name] = {'from': old_instance.get_trang_thai_display(), 'to': instance.get_trang_thai_display()}
                    elif field == 'id_nguoi_thuc_hien':
                        changes[display_name] = {'from': str(old_value) if old_value else 'Chưa có', 'to': str(new_value) if new_value else 'Chưa có'}
                    else:
                        changes[display_name] = {'from': str(old_value), 'to': str(new_value)}
            
            if changes:
                LichSuCongViec.objects.create(
                    nhiem_vu=instance,
                    user=user,
                    mo_ta=f"đã cập nhật nhiệm vụ.",
                    details=changes
                )
                # Notify assignee about the change
                if instance.id_nguoi_thuc_hien and instance.id_nguoi_thuc_hien != user:
                    Notification.objects.create(
                        user=instance.id_nguoi_thuc_hien,
                        message=f'Nhiệm vụ "{instance.ten_nhiem_vu}" bạn đang thực hiện vừa được {user.username} cập nhật.',
                        related_task=instance
                    )

@receiver(post_save, sender=Notification)
def send_email_notification(sender, instance, created, **kwargs):
    if created and instance.user.email: # Only send email for new notifications and if user has an email
        subject = f"Thông báo mới từ hệ thống: {instance.message[:50]}..."
        message = f"Bạn có một thông báo mới trong hệ thống quản lý công việc.\n\nNội dung: {instance.message}\n\nTruy cập hệ thống để xem chi tiết: http://127.0.0.1:8000/notifications/"
        send_notification_email(instance.user.email, subject, message)
