from django.conf import settings
from django.templatetags.static import static


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
