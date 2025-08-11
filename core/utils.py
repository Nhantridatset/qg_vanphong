from django.core.mail import send_mail
from django.conf import settings
from .models import Notification # Import the Notification model
from datetime import time, timedelta, datetime
import pytz

def calculate_business_hours(start_dt, end_dt):
    # Define business hours
    morning_start = time(7, 0)
    morning_end = time(11, 30)
    afternoon_start = time(13, 30)
    afternoon_end = time(17, 0)
    workdays = [0, 1, 2, 3, 4]  # Monday to Friday

    # Ensure datetimes are timezone-aware (assuming UTC if naive)
    if start_dt.tzinfo is None:
        start_dt = pytz.utc.localize(start_dt)
    if end_dt.tzinfo is None:
        end_dt = pytz.utc.localize(end_dt)

    total_seconds = 0
    
    # Clamp end_dt to be not before start_dt
    if end_dt < start_dt:
        return 0

    current_dt = start_dt
    # Iterate through each day
    while current_dt.date() <= end_dt.date():
        if current_dt.weekday() in workdays:
            day_start = current_dt.date()
            
            # Morning session
            morning_session_start = datetime.combine(day_start, morning_start, tzinfo=start_dt.tzinfo)
            morning_session_end = datetime.combine(day_start, morning_end, tzinfo=start_dt.tzinfo)
            
            overlap_start = max(current_dt, morning_session_start)
            overlap_end = min(end_dt, morning_session_end)

            if overlap_end > overlap_start:
                total_seconds += (overlap_end - overlap_start).total_seconds()

            # Afternoon session
            afternoon_session_start = datetime.combine(day_start, afternoon_start, tzinfo=start_dt.tzinfo)
            afternoon_session_end = datetime.combine(day_start, afternoon_end, tzinfo=start_dt.tzinfo)

            overlap_start = max(current_dt, afternoon_session_start)
            overlap_end = min(end_dt, afternoon_session_end)

            if overlap_end > overlap_start:
                total_seconds += (overlap_end - overlap_start).total_seconds()

        # Move to the start of the next day
        current_dt = (current_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    return round(total_seconds / 3600, 2)

def send_notification_email(recipient_email, subject, message):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        return False

def create_notification(user, message, related_task=None, related_ho_so_cong_viec=None):
    """
    Creates an in-app notification for the specified user.
    """
    Notification.objects.create(
        user=user,
        message=message,
        related_task=related_task,
        related_ho_so_cong_viec=related_ho_so_cong_viec
    )
