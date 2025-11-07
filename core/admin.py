from django.contrib import admin
from django.contrib.auth.models import Permission


# Keep admin minimal: only Users, Groups (default) and Permissions
admin.site.register(Permission)


# Customize admin site
admin.site.site_header = "Organization Management System"
admin.site.site_title = "Org Management"
admin.site.index_title = "User, Groups & Permissions"
