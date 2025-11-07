from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Organization Management'

    def ready(self):
        # Import signal handlers to ensure they are registered. Use absolute path
        # to avoid issues with relative import resolution under autoreload.
        from core import signals  # noqa: F401
