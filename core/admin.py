from django.contrib import admin, messages
from django.contrib.auth.models import Permission
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.apps import apps
from django.db import transaction
from django.http import HttpResponseForbidden
import os
import shutil


# Keep admin minimal: only Users, Groups (default) and Permissions
admin.site.register(Permission)


# Customize admin site
admin.site.site_header = getattr(settings, 'BRAND_NAME', 'Fashion Express')
admin.site.site_title = getattr(settings, 'BRAND_NAME', 'Fashion Express')
admin.site.index_title = "User, Groups & Permissions"


def _cleanup_media():
	media_root = getattr(settings, 'MEDIA_ROOT', None)
	if not media_root:
		return
	if os.path.exists(media_root):
		try:
			# remove everything under MEDIA_ROOT
			for name in os.listdir(media_root):
				path = os.path.join(media_root, name)
				if os.path.isdir(path):
					shutil.rmtree(path)
				else:
					os.remove(path)
		except Exception:
			# best-effort; don't crash the whole operation
			pass


def clean_all_data_view(request):
	"""Admin view that deletes all model data and optionally media files.

	Access restricted to superusers. Shows a confirmation page on GET,
	performs deletion on POST and redirects back to admin index.
	"""
	if not request.user.is_active or not request.user.is_superuser:
		return HttpResponseForbidden('Only superusers may perform this action.')

	if request.method == 'POST':
		# Perform deletion in a transaction; best-effort media cleanup after DB deletes
		try:
			with transaction.atomic():
				for model in apps.get_models():
					try:
						model.objects.all().delete()
					except Exception:
						# continue deleting other models even if one fails
						continue
			# cleanup media
			_cleanup_media()
			messages.success(request, 'All data deleted and media cleaned (best-effort).')
		except Exception as e:
			messages.error(request, f'Error while deleting data: {e}')
		return redirect(reverse('admin:index'))

	# GET: show confirmation
	return render(request, 'admin/clean_all_data_confirm.html', {
		'title': 'Confirm delete all data',
		'media_root': getattr(settings, 'MEDIA_ROOT', ''),
	})
