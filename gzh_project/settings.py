"""
Django settings for gzh_project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
COMPRESSED_IMG_DIR = os.path.join(STATIC_ROOT, "images/compressed/")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x&63azfscg@1a=y%!zd@^1h#g=$^8_(43=*v&azft))7l+%+h5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'south',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'gzh',
    'proxypool',
    'pure_pagination',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


PAGINATION_SETTINGS = {
    'PAGE_RANGE_DISPLAYED': 4,
    'MARGIN_PAGES_DISPLAYED': 2,
}

ROOT_URLCONF = 'gzh_project.urls'

WSGI_APPLICATION = 'gzh_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
import codecs
codecs.register(
    lambda name: codecs.lookup('utf8') if name == 'utf8mb4' else None)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': "/home/wei/.my_gzh.cnf",
            'charset': 'utf8mb4',
        }
    }
}
# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

#STATIC_URL = '/static/'
#STATIC_URL = 'http://7u2hsu.com1.z0.glb.clouddn.com/'
STATIC_URL = 'http://7u2k4s.com1.z0.glb.clouddn.com/'

STATICFILES_DIRS = (
    ("css", os.path.join(STATIC_ROOT, 'css')),
    ("js", os.path.join(STATIC_ROOT, 'js')),
    ("images", os.path.join(STATIC_ROOT, 'images')),
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    "templates",
)

# redis
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'
REDIS_PASSWORD = 'asdf_1234'
REDIS_DB = '0'

CACHE = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '%s:%s' % (REDIS_HOST, REDIS_PORT),
        'OPTIONS': {
            'DB': 1,
            #'PASSWORD': '',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            }
        },
    },
}
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
#BROKER_URL = 'redis://:%s@%s:%s/%s' %(REDIS_PASSWORD, REDIS_HOST,REDIS_PORT, REDIS_DB)

import djcelery
djcelery.setup_loader()

LOGIN_URL = '/signin/'
MOBI_TITLE = 'WeiRead'

# crontab task setting
UPDATE_CRONTAB = {"minute": 25, "hour": 19}
EMAIL_CRONTAB = {"minute": 0, "hour": 6}
LIMAGE_CRONTAB = {"minute": 0, "hour": 5}

# the first time to crawel of weixin
DAYS_AGO = 30

# redis key
IMAGES = "images"
PROXY = "proxy"

try:
    from local_settings import *
except ImportError:
    pass
