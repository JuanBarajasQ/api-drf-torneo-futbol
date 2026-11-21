"""
Configuración del proyecto.

Lee lo sensible de variables de entorno, así el mismo código corre en tu
Codespace (modo desarrollo, SQLite) y en Render (modo producción, Postgres).
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# Entorno
# ----------------------------------------------------------------------
EN_RENDER = "RENDER" in os.environ          # Render define esta variable
EN_CODESPACES = "CODESPACES" in os.environ  # GitHub Codespaces también

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "solo-para-desarrollo-cambiala-en-render",
)
DEBUG = os.environ.get("DEBUG", "False" if EN_RENDER else "True") == "True"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = []

# Render: el dominio público llega en RENDER_EXTERNAL_HOSTNAME
render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

# Codespaces: el puerto 8000 se publica en <nombre>-8000.<dominio>
codespace = os.environ.get("CODESPACE_NAME")
dominio_cs = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
if codespace and dominio_cs:
    host_cs = f"{codespace}-8000.{dominio_cs}"
    ALLOWED_HOSTS.append(host_cs)
    CSRF_TRUSTED_ORIGINS.append(f"https://{host_cs}")

# Render y Codespaces reciben la petición por HTTPS y la reenvían a Django.
# Esto hace que los enlaces que arma DRF (next, previous) salgan con https.
if EN_RENDER or EN_CODESPACES:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ----------------------------------------------------------------------
# Aplicaciones
# ----------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    # Tus apps: agrégalas aquí
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ----------------------------------------------------------------------
# Base de datos
# Sin DATABASE_URL usa SQLite (tu Codespace). En Render, DATABASE_URL
# apunta a la base Postgres.
# ----------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------
# Archivos estáticos (estilos del admin y de la API navegable)
# WhiteNoise los sirve en Render sin un servidor aparte.
# ----------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------------------------------
# Django REST Framework
# Completa este diccionario con lo que pide el contrato (paginación,
# filtros por defecto...). El esquema ya está configurado para Swagger.
# ----------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API del grupo",  # cámbialo por el nombre de tu proyecto
    "VERSION": "1.0.0",
}
