from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def has_role(user, role):
    return user.is_authenticated and user.groups.filter(name=role).exists()


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            active_roles = request.user.groups.filter(name__in=["Staff", "Doctor"]).count()
            if active_roles != 1 or not has_role(request.user, role):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
