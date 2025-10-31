# Django Production Deployment Guide (Ubuntu/Pop!_OS)

This guide sets up your app with: PostgreSQL, Gunicorn (WSGI), Nginx (reverse proxy), systemd (process manager), HTTPS (Let’s Encrypt), and secure Django settings.

Assumptions:
- OS: Ubuntu/Pop!_OS 22.04+
- Project root: /home/emarat/Downloads/org-management-main
- Python: 3.10+
- Domain: example.com (replace with yours)

---

## 1) Server prep

- Update and install base packages
```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install build-essential python3-dev python3-venv python3-pip \
                     postgresql postgresql-contrib \
                     nginx ufw curl git
```

- Create a system user (optional, safer)
```bash
sudo adduser --system --group --home /srv/orgapp orgapp
sudo mkdir -p /srv/orgapp
sudo chown -R orgapp:orgapp /srv/orgapp
```

- Copy your project to /srv/orgapp (or clone from Git)
```bash
sudo rsync -a --delete /home/emarat/Downloads/org-management-main/ /srv/orgapp/
sudo chown -R orgapp:orgapp /srv/orgapp
```

---

## 2) Python virtualenv

```bash
sudo -u orgapp bash -c '
cd /srv/orgapp
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt gunicorn psycopg2-binary whitenoise
'
```

---

## 3) Database (PostgreSQL)

- Create DB and user
```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE orgdb ENCODING 'UTF8';
CREATE USER orguser WITH PASSWORD 'change-this-strong-password';
ALTER ROLE orguser SET client_encoding TO 'utf8';
ALTER ROLE orguser SET default_transaction_isolation TO 'read committed';
ALTER ROLE orguser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE orgdb TO orguser;
SQL
```

- Optional: enable connections (usually default OK)
```bash
sudo systemctl restart postgresql
```

---

## 4) Environment variables

Create an env file readable by systemd:
```bash
sudo tee /etc/org_management.env >/dev/null <<'ENV'
DJANGO_SETTINGS_MODULE=org_management.settings
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=replace-with-a-strong-random-string
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

# PostgreSQL
DATABASE_URL=postgres://orguser:change-this-strong-password@127.0.0.1:5432/orgdb

# Static/Media
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
ENV
```

Tips:
- Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## 5) Django settings adjustments

Ensure these in org_management/settings.py (or create a settings_production.py that reads env):

```python
import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "CHANGE_ME")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# Database via DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    import dj_database_url  # pip install dj-database-url
    DATABASES = {"default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}
else:
    # fallback (not recommended for prod)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Static/Media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Optional: WhiteNoise (simple static in app)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # ...existing...
]

# Security headers (from env)
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("DJANGO_SESSION_COOKIE_SECURE", "True").lower() == "true"
CSRF_COOKIE_SECURE = os.getenv("DJANGO_CSRF_COOKIE_SECURE", "True").lower() == "true"
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").lower() == "true"
SECURE_HSTS_PRELOAD = os.getenv("DJANGO_SECURE_HSTS_PRELOAD", "True").lower() == "true"
```

Install dj-database-url if you use DATABASE_URL:
```bash
sudo -u orgapp bash -c 'source /srv/orgapp/.venv/bin/activate && pip install dj-database-url'
```

---

## 6) Collect static, migrate, create superuser

```bash
sudo -u orgapp bash -c '
cd /srv/orgapp
source .venv/bin/activate
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
'
```

---

## 7) Gunicorn (systemd)

Create service:
```bash
sudo tee /etc/systemd/system/gunicorn-orgapp.service >/dev/null <<'UNIT'
[Unit]
Description=Gunicorn for org-management
After=network.target

[Service]
User=orgapp
Group=orgapp
WorkingDirectory=/srv/orgapp
EnvironmentFile=/etc/org_management.env
ExecStart=/srv/orgapp/.venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    org_management.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-orgapp
sudo systemctl status gunicorn-orgapp --no-pager
```

Check socket:
```bash
curl -I http://127.0.0.1:8000/
```

---

## 8) Nginx (reverse proxy)

```bash
sudo tee /etc/nginx/sites-available/orgapp >/dev/null <<'NGINX'
server {
    listen 80;
    server_name example.com www.example.com;

    client_max_body_size 20M;

    location /static/ {
        alias /srv/orgapp/staticfiles/;
        access_log off;
        expires 30d;
    }

    location /media/ {
        alias /srv/orgapp/media/;
        access_log off;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/orgapp /etc/nginx/sites-enabled/orgapp
sudo nginx -t
sudo systemctl restart nginx
```

Firewall:
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 9) HTTPS (Let’s Encrypt)

```bash
sudo apt -y install certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com --agree-tos -m you@example.com --redirect
sudo systemctl status certbot.timer
```

---

## 10) Post-deploy checklist

- App health:
```bash
sudo -u orgapp bash -c 'cd /srv/orgapp && source .venv/bin/activate && python manage.py check --deploy'
curl -I https://example.com/
```

- Roles and permissions:
  - Ensure employees cannot add/edit/delete expenses; managers can.
  - Approving a claim creates an Expense with “Paid To” populated.

- Logs (tail when debugging):
```bash
journalctl -u gunicorn-orgapp -f
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

- Backups:
  - DB dump: `pg_dump -Fc orgdb > /backups/orgdb_$(date +%F).dump`
  - Media: rsync /srv/orgapp/media/

- Monitoring (optional but recommended):
  - Sentry for error reporting.
  - Uptime checks (e.g., UptimeRobot).

---

## 11) Zero-downtime updates

```bash
sudo -u orgapp bash -c '
cd /srv/orgapp
git pull --ff-only || true
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
'
sudo systemctl restart gunicorn-orgapp
sudo nginx -t && sudo systemctl reload nginx
```

---

## 12) Common pitfalls

- DEBUG must be False in production.
- Set ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS to your domain(s).
- Ensure /srv/orgapp/media/ is writable by orgapp.
- If you see TemplateSyntaxError, disable HTML format-on-save for templates or add a .prettierignore:
  - templates/**/*.html
- If Gunicorn won’t start, run the app manually to inspect errors:
```bash
sudo -u orgapp bash -c 'cd /srv/orgapp && source .venv/bin/activate && gunicorn org_management.wsgi:application --bind 127.0.0.1:8000 --log-level debug'
```

You’re ready to deploy safely and repeatably.