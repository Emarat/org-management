import os
from asgiref.wsgi import WsgiToAsgi
from django.core.wsgi import get_wsgi_application

# Ensure Django settings are set for the runtime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "org_management.settings")

# Create the Django WSGI application, then adapt it to ASGI for Vercel
_django_wsgi_app = get_wsgi_application()
app = WsgiToAsgi(_django_wsgi_app)
