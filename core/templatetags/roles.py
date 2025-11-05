from django import template

register = template.Library()

@register.filter
def has_role(user, role_name: str) -> bool:
    try:
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(name=role_name).exists()
    except Exception:
        return False
