from .base import *

DEBUG = True

INSTALLED_APPS += [
    'django_extensions',
]

# show SQL queries in terminal during development
LOGGING['loggers']['django.db.backends'] = {
    'handlers':  ['console'],
    'level':     'DEBUG',
    'propagate': False,
}