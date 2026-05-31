import os

# Provide minimal environment variables so original settings can import safely during tests
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('YOUTUBE_API_KEY', 'test-key')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('DB_NAME', 'testdb')
os.environ.setdefault('DB_USER', '')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('FRONTEND_URL', 'http://localhost')
os.environ.setdefault('BACKEND_URL', 'http://localhost')
os.environ.setdefault('EMAIL_HOST', '')
os.environ.setdefault('EMAIL_HOST_USER', '')
os.environ.setdefault('EMAIL_HOST_PASSWORD', '')

import sys
import types

# Provide a lightweight compatibility shim so Postgres-specific ArrayField
# doesn't break sqlite-based tests. We alias ArrayField -> JSONField.
try:
    from django.db import models
    fake_mod = types.ModuleType('django.contrib.postgres.fields')
    class ArrayField(models.JSONField):
        def __init__(self, base_field=None, size=None, *args, **kwargs):
            # Accept Postgres ArrayField parameters but store as JSONField for sqlite tests
            kwargs.setdefault('default', list)
            super().__init__(*args, **kwargs)
    fake_mod.ArrayField = ArrayField
    # Ensure both package and submodule are present so migration imports succeed
    fake_pkg = types.ModuleType('django.contrib.postgres')
    fake_pkg.fields = fake_mod
    sys.modules['django.contrib.postgres'] = fake_pkg
    sys.modules['django.contrib.postgres.fields'] = fake_mod
    # Also attach to the real django.contrib package if available
    try:
        import django.contrib as _djcontrib
        setattr(_djcontrib, 'postgres', fake_pkg)
    except Exception:
        pass
except Exception:
    # If django isn't importable yet, we'll let the normal import flow fail later.
    pass

# Import the normal settings (which will read env vars above), then override DB for tests
from .settings import *  # noqa: F401,F403

# Use in-memory sqlite for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use locmem email backend during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use a minimal URL conf for tests to avoid importing heavy API modules
ROOT_URLCONF = 'bookmarker.urls_test'

# Reduce INSTALLED_APPS to a minimal set to avoid importing DRF/postgres-related code during checks
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'frontend',
]

# Use default auth user for tests (avoid depending on api.CustomUser)
AUTH_USER_MODEL = 'auth.User'

# Avoid staticfiles dir warnings during tests
STATICFILES_DIRS = []
