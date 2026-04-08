from .base import *

DEBUG = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

DATABASES = {
    'default': env.db()
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
