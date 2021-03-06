"""
Django settings for websnoop project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%5sr7=$i(6z25sptiw(f+9x2wg4y2^!#5p$zjao84j8f6$2!r='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'websnoop.urls'

WSGI_APPLICATION = 'websnoop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'snoopdb',
        'USER': 'root',
        'PASSWORD' : 'Rockstand@1',
        'HOST' : 'localhost',
    }
}

MONGO_DB_IPS = ['localhost:27017']
MONGO_DBS = {'snoopinfo': {'name': 'snooptargets', 'collection': 'snoopdata', 'user': None, 'pass': None}}

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + os.path.sep + 'staticfiles'

STATICFILES_DIRS = (
    BASE_DIR + os.path.sep + "websnoop" + os.path.sep + "static",
    )

GEOIP_PATH = BASE_DIR + os.path.sep + "GeoIP" + os.path.sep + "GeoLiteCity.dat"

TEMPLATE_DIRS = (
    BASE_DIR + os.path.sep + 'websnoop' + os.path.sep,
)

MEDIA_ROOT = BASE_DIR + os.path.sep + 'mediafiles'
MEDIA_URL = '/media/'

IMAGE_UPLOAD_DIR = MEDIA_ROOT + os.path.sep

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

FILE_UPLOAD_HANDLERS = ("django.core.files.uploadhandler.MemoryFileUploadHandler", "django.core.files.uploadhandler.TemporaryFileUploadHandler")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + os.path.sep + 'logging' + os.path.sep + 'debug.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
