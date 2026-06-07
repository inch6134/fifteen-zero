from .base import *

DEBUG = True
SECRET_KEY = 'django-insecure-ch)mhk+^0^@z&(8m=$)3u)lmnu#8k9lc*v%cb_#gu!cwf9sj)w'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
