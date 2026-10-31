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
    # Options: 'garage_cdn' (default), 'github_repo' (DEPRECATED)
    'SOURCE_TYPE': os.getenv('DIGIMON_IMAGE_SOURCE_TYPE', 'garage_cdn'),

    # --- Garage CDN (current source) ---
    # Public web endpoint that serves the images, e.g. {base}/BT1-001.webp
    'GARAGE_PUBLIC_BASE_URL': os.getenv('GARAGE_PUBLIC_BASE_URL', 'https://web-garage.takaotaku.de'),

    # Optional: Garage S3 API credentials. If ALL of endpoint/bucket/key/secret
    # are set, the sync lists the bucket directly (picks up every file).
    # If any are missing, it falls back to building the expected filenames from
    # each card's JSON (cardImage + AAs/JAAs ids) and HEAD-probing the CDN.
    # Ask the Garage owners for a read-only key; the endpoint is the S3 API URL
    # (default port 3900), NOT the web endpoint above.
    'GARAGE_S3_ENDPOINT': os.getenv('GARAGE_S3_ENDPOINT', ''),
    'GARAGE_BUCKET': os.getenv('GARAGE_BUCKET', ''),
    'GARAGE_ACCESS_KEY_ID': os.getenv('GARAGE_ACCESS_KEY_ID', ''),
    'GARAGE_SECRET_ACCESS_KEY': os.getenv('GARAGE_SECRET_ACCESS_KEY', ''),
    # Must match s3_region in Garage's garage.toml.
    'GARAGE_REGION': os.getenv('GARAGE_REGION', 'garage'),
    # Optional key prefix to restrict the bucket listing.
    'GARAGE_PREFIX': os.getenv('GARAGE_PREFIX', ''),

    # Name of the DigimonCard JSONField holding the raw card JSON, used by the
    # probe fallback. Leave blank to auto-detect (works if the model has exactly
    # one JSONField).
    'CARD_JSON_FIELD': os.getenv('DIGIMON_CARD_JSON_FIELD', ''),

    # --- GitHub repo (DEPRECATED, will be removed) ---
    # Card images are no longer stored in the repo. These keys are only read
    # when SOURCE_TYPE='github_repo'.
    'GITHUB_API_URL': os.getenv(
        'DIGIMON_GITHUB_API_URL',
        'https://api.github.com/repos/TakaOtaku/Digimon-Card-App/contents/src/assets/images/cards'
    ),
    'GITHUB_BRANCH': os.getenv('DIGIMON_GITHUB_BRANCH', 'main'),
    'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN', ''),

    # -------------------------------------------------------------------------
    # STORAGE BACKEND
    # -------------------------------------------------------------------------
    # Options: 'vercel_blob', 'r2'
    'STORAGE_BACKEND': os.getenv('DIGIMON_STORAGE_BACKEND', 'r2'),

    # --- Vercel Blob (legacy / kept for reference & possible fallback) ---
    'BLOB_READ_WRITE_TOKEN': os.getenv('BLOB_READ_WRITE_TOKEN', ''),
    'BLOB_UPLOAD_ENDPOINT': os.getenv('VERCEL_BLOB_ENDPOINT', 'https://blob.vercel-storage.com'),
    'BLOB_PATH_PREFIX': 'cards/',

    # --- Cloudflare R2 (S3-compatible) ---
    'R2_ACCOUNT_ID': os.getenv('R2_ACCOUNT_ID', ''),
    'R2_ACCESS_KEY_ID': os.getenv('R2_ACCESS_KEY_ID', ''),
    'R2_SECRET_ACCESS_KEY': os.getenv('R2_SECRET_ACCESS_KEY', ''),
    'R2_BUCKET_NAME': os.getenv('R2_BUCKET_NAME', ''),
    # Public base URL for reading objects back (Public Development URL or
    # a Custom Domain attached to the bucket) — NOT the S3 API endpoint.
    'R2_PUBLIC_BASE_URL': os.getenv('R2_PUBLIC_BASE_URL', ''),
    # Key prefix inside the bucket, mirrors BLOB_PATH_PREFIX.
    'R2_PATH_PREFIX': 'cards/',

    # -------------------------------------------------------------------------
    # ALTERNATE ART PATTERN MATCHING
    # -------------------------------------------------------------------------
    # Keywords in filename that denote an Alternate Art or Promo
    # e.g., "BT1-084_P1.webp" or "BT1-084_AA.webp" or "BT1-084_PARALLEL.webp"
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