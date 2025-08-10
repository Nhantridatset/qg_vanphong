from django.core.mail import send_mail
from django.conf import settings
from .models import Notification # Import the Notification model

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
