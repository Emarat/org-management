from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Fashion Express'

    def ready(self):
        # Import signal handlers to ensure they are registered. Use absolute path
        # to avoid issues with relative import resolution under autoreload.
        from core import signals  # noqa: F401

        # No-op on supported interpreters; repairs template context copying
        # when running Django 4.2 on Python 3.13+.
        from org_management.compat import patch_template_context_copy
        patch_template_context_copy()
