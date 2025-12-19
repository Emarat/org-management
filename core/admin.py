from django.contrib import admin
from django.contrib.auth.models import Permission
from django.conf import settings


# Keep admin minimal: only Users, Groups (default) and Permissions
admin.site.register(Permission)


# Customize admin site
admin.site.site_header = getattr(settings, 'BRAND_NAME', 'Fashion Express')
admin.site.site_title = getattr(settings, 'BRAND_NAME', 'Fashion Express')
admin.site.index_title = "User, Groups & Permissions"
