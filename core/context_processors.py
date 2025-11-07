from django.conf import settings
from django.templatetags.static import static
from .models import InventoryItem
from django.db.models import F


def branding(request):
    """Provide brand information to templates (invoice/receipt headers).
    Logo is a static file path relative to /static if provided via BRAND_LOGO_FILE.
    """
    name = getattr(settings, 'BRAND_NAME', 'OrgMS')
    logo_file = getattr(settings, 'BRAND_LOGO_FILE', '')
    address = getattr(settings, 'BRAND_ADDRESS', '')
    phone = getattr(settings, 'BRAND_PHONE', '')
    email = getattr(settings, 'BRAND_EMAIL', '')

    logo_url = ''
    if logo_file:
        try:
            logo_url = static(logo_file)
        except Exception:
            logo_url = ''

    return {
        'brand': {
            'name': name,
            'logo_url': logo_url,
            'address': address,
            'phone': phone,
            'email': email,
        }
    }


def alerts(request):
    """Global lightweight alerts for templates (e.g., low stock banner)."""
    try:
        low_stock_qs = InventoryItem.objects.filter(quantity__lte=F('minimum_stock')).only('id')
        count = low_stock_qs.count()
    except Exception:
        count = 0
    return {
        'low_stock_count': count,
    }
