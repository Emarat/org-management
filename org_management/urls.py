"""
URL configuration for org_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import admin as core_admin

urlpatterns = [
    path('admin/clean-all-data/', admin.site.admin_view(core_admin.clean_all_data_view), name='admin-clean-all-data'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
