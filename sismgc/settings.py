import os
import socket
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(env_path):
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name, default=""):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _local_network_hosts():
    hosts = {"127.0.0.1", "localhost", "0.0.0.0"}
    try:
        hostname = socket.gethostname()
        hosts.add(hostname)
        hosts.add(f"{hostname}.local")
        _, _, ips = socket.gethostbyname_ex(hostname)
        hosts.update(ip for ip in ips if ip)
    except Exception:
        pass
    for target in (("8.8.8.8", 80), ("10.255.255.255", 1)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(target)
                local_ip = sock.getsockname()[0]
                if local_ip:
                    hosts.add(local_ip)
        except Exception:
            continue
    return sorted(hosts)


ENV_FILE_PATH = BASE_DIR / ".env"
_load_env_file(ENV_FILE_PATH)

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
DEBUG = _env_bool("DEBUG", True)
_allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", "127.0.0.1,localhost,0.0.0.0")
if DEBUG:
    if not _allowed_hosts_env and not ENV_FILE_PATH.exists():
        ALLOWED_HOSTS = ["*"]
    for host in _local_network_hosts():
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "core",
    "usuarios",
    "dashboard",
    "linhagens",
    "aves",
    "lotes",
    "genetica",
    "reprodutores",
    "incubacao",
    "nascimentos",
    "estoque",
    "alimentacao",
    "sanidade",
    "abate",
    "vendas",
    "financeiro",
    "relatorios",
    "historico",
    "calendario",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.CurrentUserMiddleware",
]

ROOT_URLCONF = "sismgc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.user_theme",
            ],
        },
    },
]

WSGI_APPLICATION = "sismgc.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
os.makedirs(MEDIA_ROOT, exist_ok=True)

DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "usuarios.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "login"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Base settings prepared for future PostgreSQL migration
DATABASE_ROUTERS = []

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "sismgc-local-cache",
    }
}
