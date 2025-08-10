from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import NhiemVu

class Command(BaseCommand):
    help = 'Creates new instances of recurring tasks based on their frequency.'

    def handle(self, *args, **options):
        now = timezone.now()
        recurring_tasks = NhiemVu.objects.filter(is_recurring=True)

        for task in recurring_tasks:
            # Check if a new instance needs to be created
            # This logic needs to be more sophisticated for real-world use
            # For simplicity, we'll just check if the last created task is older than its frequency
            
            # Find the latest instance of this recurring task
            latest_instance = NhiemVu.objects.filter(ten_nhiem_vu=task.ten_nhiem_vu, id_ke_hoach=task.id_ke_hoach)
            if task.id_nhiem_vu_cha:
                latest_instance = latest_instance.filter(id_nhiem_vu_cha=task.id_nhiem_vu_cha)
            latest_instance = latest_instance.order_by('-ngay_bat_dau').first()

            if not latest_instance:
                # This should not happen if the original task is recurring, but as a safeguard
                latest_instance = task

            should_create_new = False
            next_due_date = latest_instance.ngay_ket_thuc

            if task.recurring_frequency == NhiemVu.RecurringFrequency.DAILY:
                next_due_date += timedelta(days=1)
                if now.date() >= next_due_date.date():
                    should_create_new = True
            elif task.recurring_frequency == NhiemVu.RecurringFrequency.WEEKLY:
                next_due_date += timedelta(weeks=1)
                if now.date() >= next_due_date.date():
                    should_create_new = True
            elif task.recurring_frequency == NhiemVu.RecurringFrequency.MONTHLY:
                # Simple monthly logic, can be improved for exact day of month
                next_due_date += timedelta(days=30) # Approximation
                if now.date() >= next_due_date.date():
                    should_create_new = True
            elif task.recurring_frequency == NhiemVu.RecurringFrequency.YEARLY:
                next_due_date += timedelta(days=365) # Approximation
                if now.date() >= next_due_date.date():
                    should_create_new = True
            
            if should_create_new and (not task.recurring_until or next_due_date <= task.recurring_until):
                # Create a new task instance
                new_task = NhiemVu.objects.create(
                    ten_nhiem_vu=task.ten_nhiem_vu,
                    mo_ta=task.mo_ta,
                    trang_thai=NhiemVu.TrangThai.NV_CHO, # New recurring tasks start as 'Chờ duyệt giao'
                    muc_do_uu_tien=task.muc_do_uu_tien,
                    ngay_bat_dau=next_due_date, # New start date
                    ngay_ket_thuc=next_due_date + (task.ngay_ket_thuc - task.ngay_bat_dau), # Maintain duration
                    id_ke_hoach=task.id_ke_hoach,
                    id_nguoi_thuc_hien=task.id_nguoi_thuc_hien,
                    id_nhiem_vu_cha=task.id_nhiem_vu_cha,
                    thoi_gian_uoc_tinh=task.thoi_gian_uoc_tinh,
                    # Do not copy actual time or recurring settings to new instance
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created new recurring task: {new_task.ten_nhiem_vu}'))
            else:
                self.stdout.write(self.style.WARNING(f'No new recurring task needed for: {task.ten_nhiem_vu}'))
