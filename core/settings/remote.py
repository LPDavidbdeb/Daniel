from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DATABASES = {
    'default': env.db()
}

# Paramètres de sécurité de production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
