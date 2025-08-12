from django.core.mail import send_mail
from django.conf import settings
from .models import Notification # Import the Notification model
from datetime import time, timedelta, datetime
import pytz
import requests
import logging
from django.utils import timezone # Added import

logger = logging.getLogger(__name__)

def calculate_business_hours(start_dt, end_dt):
    print(f"DEBUG (utils): calculate_business_hours called with start_dt={start_dt}, end_dt={end_dt}")
    
    # Ensure datetimes are timezone-aware and convert to local timezone for calculation
    local_tz = pytz.timezone(settings.TIME_ZONE)
    if start_dt.tzinfo is None:
        start_dt = timezone.make_aware(start_dt, timezone=local_tz)
    else:
        start_dt = start_dt.astimezone(local_tz)
    
    if end_dt.tzinfo is None:
        end_dt = timezone.make_aware(end_dt, timezone=local_tz)
    else:
        end_dt = end_dt.astimezone(local_tz)

    print(f"DEBUG (utils): Converted to local timezone: start_dt={start_dt}, end_dt={end_dt}")

    # Define business hours (these are local times)
    morning_start = time(7, 0)
    morning_end = time(11, 30)
    afternoon_start = time(13, 30)
    afternoon_end = time(17, 0)
    workdays = [0, 1, 2, 3, 4]  # Monday to Friday

    total_seconds = 0
    
    # Clamp end_dt to be not before start_dt
    if end_dt < start_dt:
        print(f"DEBUG (utils): end_dt ({end_dt}) is before start_dt ({start_dt}). Returning 0.")
        return 0

    # Iterate through each day from start_dt's day to end_dt's day
    current_day = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    while current_day.date() <= end_dt.date():
        if current_day.weekday() in workdays:
            # Morning session for the current day
            morning_session_start = datetime.combine(current_day.date(), morning_start, tzinfo=local_tz) # Use local_tz
            morning_session_end = datetime.combine(current_day.date(), morning_end, tzinfo=local_tz) # Use local_tz
            
            # Calculate overlap with task duration
            overlap_start_morning = max(start_dt, morning_session_start)
            overlap_end_morning = min(end_dt, morning_session_end)

            if overlap_end_morning > overlap_start_morning:
                total_seconds += (overlap_end_morning - overlap_start_morning).total_seconds()

            # Afternoon session
            afternoon_session_start = datetime.combine(current_day.date(), afternoon_start, tzinfo=local_tz) # Use local_tz
            afternoon_session_end = datetime.combine(current_day.date(), afternoon_end, tzinfo=local_tz) # Use local_tz

            # Calculate overlap with task duration
            overlap_start_afternoon = max(start_dt, afternoon_session_start)
            overlap_end_afternoon = min(end_dt, afternoon_session_end)

            if overlap_end_afternoon > overlap_start_afternoon:
                total_seconds += (overlap_end_afternoon - overlap_start_afternoon).total_seconds()

        # Move to the start of the next day
        current_day += timedelta(days=1)

    print(f"DEBUG (utils): total_seconds={total_seconds}, total_hours={round(total_seconds / 3600, 2)}")
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

def send_zalo_message(zalo_user_id, message_text):
    """
    Sends a text message to a Zalo user via Zalo Official Account API.
    Requires ZALO_OA_ID and ZALO_ACCESS_TOKEN to be set in Django settings.
    """
    if not settings.ZALO_OA_ID or not settings.ZALO_ACCESS_TOKEN:
        logger.error("Zalo API credentials (ZALO_OA_ID or ZALO_ACCESS_TOKEN) are not set in settings.")
        return False

    url = f"https://openapi.zalo.me/v2.0/oa/message"
    headers = {
        "access_token": settings.ZALO_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {
            "user_id": zalo_user_id
        },
        "message": {
            "text": message_text
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()
        if result.get("error") == 0:
            logger.info(f"Zalo message sent successfully to {zalo_user_id}: {result}")
            return True
        else:
            logger.error(f"Failed to send Zalo message to {zalo_user_id}: {result}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Zalo message to {zalo_user_id}: {e}")
        return False