from notifications.models import Notification
from students.models import Parent

def send_smart_notification(student, title, message, link=None):
    """
    Sends notification to student and all associated parents.
    """
    # 1. Notify Student User
    if student and hasattr(student, 'user') and student.user:
        Notification.objects.create(
            user=student.user,
            title=title,
            message=message,
            link=link or '/dashboard/'
        )

    # 2. Notify Parent Users
    if student:
        parents = Parent.objects.filter(students=student)
        for parent in parents:
            if hasattr(parent, 'user') and parent.user:
                Notification.objects.create(
                    user=parent.user,
                    title=title,
                    message=message,
                    link=link or '/parent-dashboard/'
                )

def send_user_notification(user, title, message, link=None):
    """
    Sends notification to a specific user.
    """
    if user:
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            link=link or '/dashboard/'
        )
