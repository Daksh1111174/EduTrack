from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    """Decorator for views that checks whether a user has one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You do not have permission to access that page.")
            return redirect('dashboard')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required('ADMIN')(view_func)

def teacher_required(view_func):
    return role_required('TEACHER', 'ADMIN')(view_func)

def student_required(view_func):
    return role_required('STUDENT', 'ADMIN')(view_func)

def parent_required(view_func):
    return role_required('PARENT', 'ADMIN')(view_func)
