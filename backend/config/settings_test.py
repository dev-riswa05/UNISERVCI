"""Réglages des tests : SQLite en mémoire, sans MySQL ni .env.

Usage : python manage.py test --settings=config.settings_test
Les vraies migrations sont exécutées sur une base neuve.
"""
import os

os.environ.setdefault('DJANGO_DEBUG', 'True')

from .settings import *  # noqa: E402,F401,F403


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SECURE_SSL_REDIRECT = False
ALLOWED_HOSTS = ['testserver', 'localhost']
