import mimetypes
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings

from analytics.models import CardImage
from .sync_card_images import Command as SyncCommand


class Command(SyncCommand):
    """
    One-time migration: move existing CardImage rows that were uploaded to
    Vercel Blob over to Cloudflare R2, and update image_url / storage_backend
    to match.

    Since the Vercel Blob store may currently be blocked (rate/quota limit),
    each image is fetched with a fallback chain:
      1. Try the existing image_url on Vercel Blob directly.
      2. If that fails, re-fetch the original file from the GitHub source repo.

    This does NOT touch cards that have no CardImage at all yet — use
    `sync_card_images --only-missing` for those.
    """

    help = (
        "Migrate CardImage rows with storage_backend='vercel_blob' to R2, "
        "falling back to the original GitHub source if Vercel Blob is unreachable."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without uploading to R2 or writing to the DB.',
        )
        parser.add_argument(
            '--source',
            choices=['auto', 'vercel', 'github'],
            default='auto',
            help=(
                "Where to fetch image bytes from. 'auto' (default) tries Vercel Blob "
                "first and falls back to GitHub. 'github' skips the Vercel attempt "
                "entirely (recommended while the store is known to be blocked). "
                "'vercel' only tries Vercel Blob (useful to check if it's unblocked yet)."
            ),
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Only process the first N rows (useful for a quick test run).',
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=8,
            help='Number of concurrent download/upload threads (default: 8).',
        )

    def handle(self, *args, **options):
        sync_config = getattr(settings, 'DIGIMON_IMAGE_SYNC', {})
        dry_run = options['dry_run']
        source_mode = options['source']
        limit = options['limit']
        workers = max(1, options['workers'])
        output_lock = threading.Lock()

        # --- Validate R2 config (uploads use a raw signed HTTP PUT, no client to build) ---
        r2_account_id = sync_config.get('R2_ACCOUNT_ID')
        r2_access_key = sync_config.get('R2_ACCESS_KEY_ID')
        r2_secret_key = sync_config.get('R2_SECRET_ACCESS_KEY')
        r2_bucket = sync_config.get('R2_BUCKET_NAME')
        r2_public_base_url = sync_config.get('R2_PUBLIC_BASE_URL')
        r2_path_prefix = sync_config.get('R2_PATH_PREFIX', 'cards/')

        missing = [
            name for name, val in [
                ('R2_ACCOUNT_ID', r2_account_id),
                ('R2_ACCESS_KEY_ID', r2_access_key),
                ('R2_SECRET_ACCESS_KEY', r2_secret_key),
                ('R2_BUCKET_NAME', r2_bucket),
                ('R2_PUBLIC_BASE_URL', r2_public_base_url),
            ] if not val
        ]
        if missing:
            self.stderr.write(self.style.ERROR(f"Missing R2 config in DIGIMON_IMAGE_SYNC / env: {', '.join(missing)}"))
            return

        # --- Resolve GitHub source pieces for the fallback path ---
        github_api_url = sync_config.get('GITHUB_API_URL')
        branch = sync_config.get('GITHUB_BRANCH', 'main')

        match = self.GITHUB_CONTENTS_URL_RE.search(github_api_url)
        if not match:
            self.stderr.write(self.style.ERROR(f"Could not parse GITHUB_API_URL: {github_api_url}"))
            return
        owner = match.group('owner')
        repo = match.group('repo')
        images_path = match.group('path').rstrip('/')

        # --- Gather rows to migrate ---
        queryset = CardImage.objects.filter(storage_backend='vercel_blob').select_related('card').order_by('id')
        if limit:
            queryset = queryset[:limit]

        rows = list(queryset)  # materialize once — this is our work list, no further DB reads needed per-row
        total = len(rows) if limit else CardImage.objects.filter(storage_backend='vercel_blob').count()
        self.stdout.write(
            f"Found {total} CardImage row(s) on Vercel Blob to migrate. "
            f"Source mode: {source_mode}. Workers: {workers}."
        )

        if dry_run:
            for img in rows:
                self.stdout.write(f"[dry-run] Would migrate {img.source_filename} (card {img.card.card_number})")
            self.stdout.write(self.style.SUCCESS(f"\n[dry-run] {len(rows)} row(s) would be migrated."))
            return

        def fetch_bytes(img):
            """Runs in a worker thread. Returns raw image bytes via the fallback chain. No DB access."""
            filename = img.source_filename

            if source_mode in ('auto', 'vercel'):
                try:
                    res = requests.get(img.image_url, timeout=15)
                    if res.status_code == 200:
                        return res.content
                    elif source_mode == 'vercel':
                        raise RuntimeError(f"Vercel fetch failed ({res.status_code})")
                except requests.RequestException as e:
                    if source_mode == 'vercel':
                        raise RuntimeError(f"Vercel fetch error: {e}")

            if source_mode in ('auto', 'github'):
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{images_path}/{filename}"
                res = requests.get(raw_url, timeout=15)
                if res.status_code == 200:
                    return res.content
                raise RuntimeError(f"GitHub fallback failed ({res.status_code})")

            raise RuntimeError("Could not obtain image bytes (no source succeeded).")

        def worker(img):
            image_bytes = fetch_bytes(img)
            mime_type = mimetypes.guess_type(img.source_filename)[0] or "image/png"
            key = f"{r2_path_prefix.strip('/')}/{img.source_filename}"
            public_url = self.upload_to_r2(
                r2_account_id, r2_access_key, r2_secret_key,
                r2_bucket, key, image_bytes, mime_type, r2_public_base_url,
            )
            return public_url

        migrated = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_img = {executor.submit(worker, img): img for img in rows}

            for future in as_completed(future_to_img):
                img = future_to_img[future]
                filename = img.source_filename
                card_number = img.card.card_number

                try:
                    public_url = future.result()
                except Exception as e:
                    failed += 1
                    with output_lock:
                        self.stderr.write(
                            self.style.ERROR(f"Failed to migrate {filename} (card {card_number}): {e}")
                        )
                    continue

                # DB write stays on the main thread.
                img.image_url = public_url
                img.storage_backend = 'r2'
                img.save(update_fields=['image_url', 'storage_backend'])

                migrated += 1
                with output_lock:
                    self.stdout.write(self.style.SUCCESS(f"Migrated {filename} ({card_number}) -> {public_url}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nMigration complete. Migrated: {migrated}, Failed: {failed}, Total: {total}")
        )