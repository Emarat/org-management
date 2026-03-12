from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.apps import apps
from django.db import transaction
from django.http import HttpResponseForbidden
from django.contrib.sessions.models import Session
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
		return False
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
		return True
	return False


def _is_checked(post_data, key):
	return post_data.get(key) in {'1', 'true', 'on', 'yes'}


def _safe_delete(label, queryset, deleted_summary, errors):
	try:
		deleted_count, _details = queryset.delete()
		deleted_summary.append((label, deleted_count))
	except Exception as exc:
		errors.append(f'{label}: {exc}')


def _core_models():
	try:
		return list(apps.get_app_config('core').get_models())
	except LookupError:
		return []


def _model_count(model):
	try:
		return model.objects.count()
	except Exception:
		return None


def _cleanup_options_from_data(data):
	return {
		'delete_core_data': _is_checked(data, 'delete_core_data'),
		'delete_non_superusers': _is_checked(data, 'delete_non_superusers'),
		'delete_superusers': _is_checked(data, 'delete_superusers'),
		'preserve_current_superuser': _is_checked(data, 'preserve_current_superuser'),
		'delete_groups': _is_checked(data, 'delete_groups'),
		'delete_permissions': _is_checked(data, 'delete_permissions'),
		'delete_sessions': _is_checked(data, 'delete_sessions'),
		'delete_admin_logs': _is_checked(data, 'delete_admin_logs'),
		'delete_axes_logs': _is_checked(data, 'delete_axes_logs'),
		'delete_media_files': _is_checked(data, 'delete_media_files'),
	}


def _default_cleanup_options():
	return {
		'delete_core_data': True,
		'delete_non_superusers': False,
		'delete_superusers': False,
		'preserve_current_superuser': True,
		'delete_groups': False,
		'delete_permissions': False,
		'delete_sessions': False,
		'delete_admin_logs': False,
		'delete_axes_logs': False,
		'delete_media_files': False,
	}


def _is_any_cleanup_option_selected(options):
	return any([
		options['delete_core_data'],
		options['delete_non_superusers'],
		options['delete_superusers'],
		options['delete_groups'],
		options['delete_permissions'],
		options['delete_sessions'],
		options['delete_admin_logs'],
		options['delete_axes_logs'],
		options['delete_media_files'],
	])


def _build_context(request, cleanup_options, preview_rows=None, preview_warnings=None):
	core_model_rows = []
	for model in _core_models():
		core_model_rows.append({
			'label': f'{model._meta.app_label}.{model.__name__}',
			'count': _model_count(model),
		})

	UserModel = get_user_model()
	return {
		'title': 'Data cleanup options',
		'media_root': getattr(settings, 'MEDIA_ROOT', ''),
		'core_model_rows': core_model_rows,
		'non_superuser_count': UserModel.objects.filter(is_superuser=False).count(),
		'superuser_count': UserModel.objects.filter(is_superuser=True).count(),
		'current_superuser': request.user,
		'group_count': Group.objects.count(),
		'permission_count': Permission.objects.count(),
		'session_count': Session.objects.count(),
		'admin_log_count': LogEntry.objects.count(),
		'cleanup_options': cleanup_options,
		'preview_rows': preview_rows or [],
		'preview_warnings': preview_warnings or [],
	}


def _build_preview_rows(request, options):
	rows = []
	warnings = []
	UserModel = get_user_model()

	if options['delete_core_data']:
		for model in _core_models():
			label = f'{model._meta.app_label}.{model.__name__}'
			rows.append((label, _model_count(model), 'db records'))

	if options['delete_non_superusers']:
		rows.append((
			f'{UserModel._meta.app_label}.{UserModel.__name__} (non-superusers)',
			UserModel.objects.filter(is_superuser=False).count(),
			'db records',
		))

	if options['delete_superusers']:
		superusers_qs = UserModel.objects.filter(is_superuser=True)
		if options['preserve_current_superuser']:
			superusers_qs = superusers_qs.exclude(pk=request.user.pk)
		else:
			warnings.append('Current logged-in superuser will also be deleted.')
		rows.append((
			f'{UserModel._meta.app_label}.{UserModel.__name__} (superusers)',
			superusers_qs.count(),
			'db records',
		))

	if options['delete_groups']:
		rows.append(('auth.Group', Group.objects.count(), 'db records'))

	if options['delete_permissions']:
		rows.append(('auth.Permission', Permission.objects.count(), 'db records'))

	if options['delete_sessions']:
		rows.append(('sessions.Session', Session.objects.count(), 'db records'))

	if options['delete_admin_logs']:
		rows.append(('admin.LogEntry', LogEntry.objects.count(), 'db records'))

	if options['delete_axes_logs']:
		try:
			for model in apps.get_app_config('axes').get_models():
				rows.append((f'{model._meta.app_label}.{model.__name__}', _model_count(model), 'db records'))
		except LookupError:
			warnings.append('axes app is not installed in this environment.')

	if options['delete_media_files']:
		rows.append(('media files', None, 'files under MEDIA_ROOT (best-effort)'))

	return rows, warnings


def clean_all_data_view(request):
	"""Admin view that deletes all model data and optionally media files.

	Access restricted to superusers. Shows a confirmation page on GET,
	performs deletion on POST and redirects back to admin index.
	"""
	if not request.user.is_active or not request.user.is_superuser:
		return HttpResponseForbidden('Only superusers may perform this action.')

	if request.method == 'POST':
		cleanup_options = _cleanup_options_from_data(request.POST)
		action = (request.POST.get('action') or 'execute').strip().lower()

		if not _is_any_cleanup_option_selected(cleanup_options):
			messages.warning(request, 'No cleanup option selected. Nothing was deleted.')
			return redirect(reverse('admin-clean-all-data'))

		if action == 'preview':
			preview_rows, preview_warnings = _build_preview_rows(request, cleanup_options)
			context = _build_context(
				request,
				cleanup_options,
				preview_rows=preview_rows,
				preview_warnings=preview_warnings,
			)
			return render(request, 'admin/clean_all_data_confirm.html', context)

		if cleanup_options['delete_superusers'] and not cleanup_options['preserve_current_superuser']:
			danger_phrase = (request.POST.get('danger_confirm') or '').strip()
			if danger_phrase != 'DELETE_SUPERUSERS':
				messages.error(
					request,
					'To delete superusers (including your own account), type DELETE_SUPERUSERS exactly.',
				)
				return redirect(reverse('admin-clean-all-data'))

		deleted_summary = []
		errors = []

		try:
			with transaction.atomic():
				if cleanup_options['delete_core_data']:
					for model in _core_models():
						label = f'{model._meta.app_label}.{model.__name__}'
						_safe_delete(label, model.objects.all(), deleted_summary, errors)

				UserModel = get_user_model()
				if cleanup_options['delete_non_superusers']:
					_safe_delete(
						f'{UserModel._meta.app_label}.{UserModel.__name__} (non-superusers)',
						UserModel.objects.filter(is_superuser=False),
						deleted_summary,
						errors,
					)

				if cleanup_options['delete_superusers']:
					superusers_qs = UserModel.objects.filter(is_superuser=True)
					if cleanup_options['preserve_current_superuser']:
						superusers_qs = superusers_qs.exclude(pk=request.user.pk)
					_safe_delete(
						f'{UserModel._meta.app_label}.{UserModel.__name__} (superusers)',
						superusers_qs,
						deleted_summary,
						errors,
					)

				if cleanup_options['delete_groups']:
					_safe_delete('auth.Group', Group.objects.all(), deleted_summary, errors)

				if cleanup_options['delete_permissions']:
					_safe_delete('auth.Permission', Permission.objects.all(), deleted_summary, errors)

				if cleanup_options['delete_sessions']:
					_safe_delete('sessions.Session', Session.objects.all(), deleted_summary, errors)

				if cleanup_options['delete_admin_logs']:
					_safe_delete('admin.LogEntry', LogEntry.objects.all(), deleted_summary, errors)

				if cleanup_options['delete_axes_logs']:
					try:
						for model in apps.get_app_config('axes').get_models():
							label = f'{model._meta.app_label}.{model.__name__}'
							_safe_delete(label, model.objects.all(), deleted_summary, errors)
					except LookupError:
						errors.append('axes app is not installed in this environment.')
		except Exception as exc:
			errors.append(f'Unexpected cleanup error: {exc}')

		if cleanup_options['delete_media_files']:
			media_cleaned = _cleanup_media()
			if media_cleaned:
				deleted_summary.append(('media files', -1))

		if deleted_summary:
			summary_parts = []
			for label, count in deleted_summary:
				if count == -1:
					summary_parts.append(f'{label}: cleaned')
				else:
					summary_parts.append(f'{label}: {count} deleted')
			messages.success(request, 'Cleanup completed. ' + '; '.join(summary_parts))
		else:
			messages.info(request, 'Cleanup completed. No matching records found.')

		for err in errors:
			messages.error(request, err)

		return redirect(reverse('admin:index'))

	# GET: show confirmation
	return render(
		request,
		'admin/clean_all_data_confirm.html',
		_build_context(request, _default_cleanup_options()),
	)
