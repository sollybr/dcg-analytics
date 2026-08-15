import mimetypes
import requests

from django.conf import settings
from botocore.exceptions import ClientError

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

    def handle(self, *args, **options):
        sync_config = getattr(settings, 'DIGIMON_IMAGE_SYNC', {})
        dry_run = options['dry_run']
        source_mode = options['source']
        limit = options['limit']

        # --- Validate & build R2 client (reused from sync_card_images.Command) ---
        r2_bucket = sync_config.get('R2_BUCKET_NAME')
        r2_public_base_url = sync_config.get('R2_PUBLIC_BASE_URL')
        r2_path_prefix = sync_config.get('R2_PATH_PREFIX', 'cards/')

        missing = [
            name for name, val in [
                ('R2_ACCOUNT_ID', sync_config.get('R2_ACCOUNT_ID')),
                ('R2_ACCESS_KEY_ID', sync_config.get('R2_ACCESS_KEY_ID')),
                ('R2_SECRET_ACCESS_KEY', sync_config.get('R2_SECRET_ACCESS_KEY')),
                ('R2_BUCKET_NAME', r2_bucket),
                ('R2_PUBLIC_BASE_URL', r2_public_base_url),
            ] if not val
        ]
        if missing:
            self.stderr.write(self.style.ERROR(f"Missing R2 config in DIGIMON_IMAGE_SYNC / env: {', '.join(missing)}"))
            return

        r2_client = self.build_r2_client(sync_config)

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

        total = queryset.count() if not limit else min(limit, CardImage.objects.filter(storage_backend='vercel_blob').count())
        self.stdout.write(f"Found {total} CardImage row(s) on Vercel Blob to migrate. Source mode: {source_mode}")

        migrated = 0
        failed = 0

        for img in queryset:
            filename = img.source_filename
            card_number = img.card.card_number
            image_bytes = None

            if source_mode in ('auto', 'vercel'):
                try:
                    res = requests.get(img.image_url, timeout=15)
                    if res.status_code == 200:
                        image_bytes = res.content
                    elif source_mode == 'vercel':
                        self.stderr.write(
                            self.style.ERROR(f"Vercel fetch failed for {filename} ({res.status_code}); skipping (source=vercel).")
                        )
                except requests.RequestException as e:
                    if source_mode == 'vercel':
                        self.stderr.write(self.style.ERROR(f"Vercel fetch error for {filename}: {e}; skipping (source=vercel)."))

            if image_bytes is None and source_mode in ('auto', 'github'):
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{images_path}/{filename}"
                try:
                    res = requests.get(raw_url, timeout=15)
                    if res.status_code == 200:
                        image_bytes = res.content
                    else:
                        self.stderr.write(
                            self.style.ERROR(f"GitHub fallback failed for {filename} ({res.status_code}).")
                        )
                except requests.RequestException as e:
                    self.stderr.write(self.style.ERROR(f"GitHub fallback error for {filename}: {e}"))

            if image_bytes is None:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f"Could not obtain bytes for {filename} (card {card_number}); skipping.")
                )
                continue

            mime_type = mimetypes.guess_type(filename)[0] or "image/png"
            key = f"{r2_path_prefix.strip('/')}/{filename}"

            if dry_run:
                self.stdout.write(
                    f"[dry-run] Would migrate {filename} ({len(image_bytes)} bytes, card {card_number}) "
                    f"-> r2://{r2_bucket}/{key}"
                )
                migrated += 1
                continue

            try:
                public_url = self.upload_to_r2(r2_client, r2_bucket, key, image_bytes, mime_type, r2_public_base_url)
            except ClientError as e:
                failed += 1
                self.stderr.write(self.style.ERROR(f"R2 upload failed for {filename}: {e}"))
                continue

            img.image_url = public_url
            img.storage_backend = 'r2'
            img.save(update_fields=['image_url', 'storage_backend'])

            migrated += 1
            self.stdout.write(self.style.SUCCESS(f"Migrated {filename} ({card_number}) -> {public_url}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nMigration complete. Migrated: {migrated}, Failed: {failed}, Total: {total}")
        )