from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

ROLE_OWNER = 'Owner'
ROLE_MANAGER = 'Manager'
ROLE_FINANCE = 'Finance'
ROLE_EMPLOYEE = 'Employee'


def user_in_group(user, group_name: str) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_superuser if group_name == ROLE_OWNER else user.groups.filter(name=group_name).exists()


def user_has_any_role(user, roles) -> bool:
    if not user.is_authenticated:
        return False
    # Superuser always passes
    if user.is_superuser:
        return True
    for r in roles:
        if user_in_group(user, r):
            return True
    return False


def role_required(*roles, allow_superuser: bool = True):
    """Decorator to require membership in any of the given roles.
    Usage: @role_required(ROLE_MANAGER, ROLE_FINANCE)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url='/login/')
            if allow_superuser and user.is_superuser:
                return view_func(request, *args, **kwargs)
            if not user_has_any_role(user, roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
