import os
import dj_database_url

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CRON_SECRET = os.getenv("CRON_SECRET", "default-dev-token")
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-digimon-stats-key-12345')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['.vercel.app', '127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if os.environ.get('DATABASE_URL'):
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.parse(
            os.environ['DATABASE_URL'],
            conn_max_age=0,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

DIGIMON_IMAGE_SYNC = {
    # -------------------------------------------------------------------------
    # SOURCE CONFIGURATION
    # -------------------------------------------------------------------------
    'SOURCE_TYPE': os.getenv('DIGIMON_IMAGE_SOURCE_TYPE', 'github_repo'),
    'GITHUB_API_URL': os.getenv(
        'DIGIMON_GITHUB_API_URL',
        'https://api.github.com/repos/TakaOtaku/Digimon-Card-App/contents/src/assets/images/cards'
    ),
    # Branch to read from when fetching the full file tree via GitHub's
    # Git Trees API (used to get past the Contents API's ~1000-entry cap
    # on large directories).
    'GITHUB_BRANCH': os.getenv('DIGIMON_GITHUB_BRANCH', 'main'),

    # -------------------------------------------------------------------------
    # STORAGE BACKEND
    # -------------------------------------------------------------------------
    # Options: 'vercel_blob', 's3', 'database'
    'STORAGE_BACKEND': os.getenv('DIGIMON_STORAGE_BACKEND', 'vercel_blob'),
    'BLOB_READ_WRITE_TOKEN': os.getenv('BLOB_READ_WRITE_TOKEN', ''),
    'BLOB_UPLOAD_ENDPOINT': os.getenv('VERCEL_BLOB_ENDPOINT', 'https://blob.vercel-storage.com'),
    'BLOB_PATH_PREFIX': 'cards/',

    # -------------------------------------------------------------------------
    # ALTERNATE ART PATTERN MATCHING
    # -------------------------------------------------------------------------
    # Keywords in filename that denote an Alternate Art or Promo
    # e.g., "BT1-084_P1.png" or "BT1-084_AA.png" or "BT1-084_PARALLEL.png"
    'ALT_ART_INDICATORS': ['_P', '_AA', '_PARALLEL', '_PROMO', '_ALT'],
}

ROOT_URLCONF = 'digimon_stats.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'digimon_stats.wsgi.app'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'digimon-cache',
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]