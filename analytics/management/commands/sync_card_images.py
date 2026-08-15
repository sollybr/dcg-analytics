import os
import re
import mimetypes
import requests
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from django.core.management.base import BaseCommand
from django.conf import settings

from analytics.models import DigimonCard, CardImage


class Command(BaseCommand):
    help = "Sync card images from the configured source (GitHub repo by default) to the configured storage backend, linking them to DigimonCard via CardImage."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-upload and overwrite images that were already synced.',
        )
        parser.add_argument(
            '--only-missing',
            action='store_true',
            help=(
                'Only sync cards that have no CardImage records at all yet. '
                'Skips any card with at least one existing image, regardless '
                'of which storage backend it was uploaded to. Cannot be '
                'combined with --force.'
            ),
        )

    # Matches the actual card number prefix, e.g. "BT1-084", "AD1-004", "EX2-010".
    # Anything after this match is suffix metadata (variant markers, language
    # tags, etc.) rather than part of the card number itself.
    CARD_NUMBER_RE = re.compile(r'^([A-Za-z]+\d*-\d+)')

    # Matches https://api.github.com/repos/{owner}/{repo}/contents/{path}
    # so we can derive the pieces needed for the Git Trees API without
    # requiring new settings keys.
    GITHUB_CONTENTS_URL_RE = re.compile(
        r'repos/(?P<owner>[^/]+)/(?P<repo>[^/]+)/contents/(?P<path>.+?)/?$'
    )

    def _github_get_with_retry(self, url, headers, attempts=3):
        """
        GET with basic retry/backoff for transient GitHub API errors.
        The Trees API occasionally returns a bare 500 (not a documented
        status for this endpoint) under load; a short retry clears most
        of these without any special-casing.
        """
        import time
        last_response = None
        for attempt in range(attempts):
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp
            last_response = resp
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, ...
        return last_response

    def fetch_all_repo_files(self, github_api_url, branch, github_token=None):
        """
        Fetch the file list for the configured GitHub images folder using
        the Git Trees API, scoped to just that folder rather than the whole
        repo.

        Fetching the entire repo recursively (recursive=1 from the root)
        pulls in all source code alongside the images and is a much larger,
        heavier request — for a full app repo this occasionally returns a
        bare 500 from GitHub. Instead, we walk down the path segments with
        small non-recursive lookups to find the target folder's own tree
        SHA, then do one recursive=1 call scoped to just that folder.
        """
        match = self.GITHUB_CONTENTS_URL_RE.search(github_api_url)
        if not match:
            raise ValueError(
                f"Could not parse owner/repo/path from GITHUB_API_URL: {github_api_url}"
            )
        owner = match.group('owner')
        repo = match.group('repo')
        images_path = match.group('path')

        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        path_parts = [p for p in images_path.split('/') if p]
        current_sha = branch  # the Trees API accepts a branch/ref name at the root

        # Walk down to the target folder, resolving one path segment at a time.
        for part in path_parts:
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{current_sha}"
            self.stdout.write(f"Resolving path segment '{part}' via {url}...")
            resp = self._github_get_with_retry(url, headers)
            if resp is None or resp.status_code != 200:
                status = resp.status_code if resp is not None else 'no response'
                body = resp.text if resp is not None else ''
                raise RuntimeError(
                    f"GitHub Trees API request failed ({status}) while resolving '{part}': {body}"
                )
            data = resp.json()
            entry = next(
                (e for e in data.get('tree', []) if e.get('path') == part and e.get('type') == 'tree'),
                None,
            )
            if not entry:
                raise RuntimeError(f"Could not find folder '{part}' while resolving path '{images_path}'.")
            current_sha = entry['sha']

        # current_sha now points at the target folder itself. Fetch its
        # contents recursively (harmless even if it's flat, and handles the
        # case where card art ends up organized into subfolders later).
        final_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{current_sha}?recursive=1"
        self.stdout.write(f"Fetching image folder tree from {final_url}...")
        resp = self._github_get_with_retry(final_url, headers)
        if resp is None or resp.status_code != 200:
            status = resp.status_code if resp is not None else 'no response'
            body = resp.text if resp is not None else ''
            raise RuntimeError(f"GitHub Trees API request failed ({status}): {body}")

        tree_data = resp.json()
        if tree_data.get('truncated'):
            self.stderr.write(
                self.style.WARNING(
                    "GitHub reports this tree response was truncated. Some files may be missed — "
                    "consider organizing card art into subfolders to keep each request smaller."
                )
            )

        files = []
        for item in tree_data.get('tree', []):
            if item.get('type') != 'blob':
                continue
            path = item.get('path', '')
            filename = path.rsplit('/', 1)[-1]
            full_repo_path = f"{images_path.rstrip('/')}/{path}"
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{full_repo_path}"
            files.append({
                "name": filename,
                "download_url": raw_url,
                "type": "file",
            })

        return files

    def parse_card_number(self, filename, alt_indicators):
        """
        Extract base card_number and identify variant type from a filename.
        Front-anchors on the real card number pattern rather than trying to
        strip known suffixes from the end, since suffixes can be chained in
        ways that don't put the variant marker last (e.g. a language tag
        appended after the variant marker).

        Examples:
            "BT1-084.png"        -> ("BT1-084", "standard")
            "BT1-084_P1.png"     -> ("BT1-084", "alternate_art")
            "BT1-084_AA.png"     -> ("BT1-084", "alternate_art")
            "AD1-004_P1-J.webp"  -> ("AD1-004", "alternate_art")
        """
        name_without_ext = os.path.splitext(filename)[0]

        match = self.CARD_NUMBER_RE.match(name_without_ext)
        base_card_number = match.group(1) if match else name_without_ext
        suffix = name_without_ext[len(base_card_number):]

        is_alt = any(ind.upper() in suffix.upper() for ind in alt_indicators)
        variant_type = 'alternate_art' if is_alt else 'standard'

        return base_card_number, variant_type

    def build_r2_client(self, sync_config):
        """
        Build a boto3 client pointed at Cloudflare R2's S3-compatible endpoint.
        R2 requires region_name='auto' and the account-scoped endpoint URL —
        everything else matches standard S3 usage.
        """
        account_id = sync_config.get('R2_ACCOUNT_ID')
        access_key = sync_config.get('R2_ACCESS_KEY_ID')
        secret_key = sync_config.get('R2_SECRET_ACCESS_KEY')

        return boto3.client(
            's3',
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='auto',
            config=BotoConfig(signature_version='s3v4'),
        )

    def upload_to_r2(self, client, bucket, key, image_bytes, mime_type, public_base_url):
        """Upload bytes to R2 and return the public URL for the object."""
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=image_bytes,
            ContentType=mime_type,
        )
        return f"{public_base_url.rstrip('/')}/{key}"

    def upload_to_vercel_blob(self, image_bytes, filename, mime_type, blob_token, upload_endpoint, path_prefix):
        """Upload bytes to Vercel Blob and return the public URL, or None on failure."""
        target_url = f"{upload_endpoint.rstrip('/')}/{path_prefix.strip('/')}/{filename}"
        headers = {
            "Authorization": f"Bearer {blob_token}",
            "x-api-version": "7",
            "x-add-random-suffix": "0",
            "x-access": "public",
            "x-content-type": mime_type,
        }
        blob_res = requests.put(target_url, data=image_bytes, headers=headers)
        if blob_res.status_code not in (200, 201):
            self.stderr.write(
                self.style.ERROR(f"Vercel Blob upload failed for {filename}: {blob_res.status_code} {blob_res.text}")
            )
            return None
        return blob_res.json().get("url")

    def handle(self, *args, **options):
        sync_config = getattr(settings, 'DIGIMON_IMAGE_SYNC', {})
        force = options['force'] or sync_config.get('OVERWRITE_EXISTING', False)
        only_missing = options['only_missing']

        if force and only_missing:
            self.stderr.write(self.style.ERROR("--force and --only-missing are mutually exclusive."))
            return

        source_type = sync_config.get('SOURCE_TYPE', 'github_repo')
        github_api_url = sync_config.get('GITHUB_API_URL')

        storage_backend = sync_config.get('STORAGE_BACKEND', 'r2')
        alt_indicators = sync_config.get('ALT_ART_INDICATORS', ['_P', '_AA', '_PARALLEL', '_PROMO', '_ALT'])

        r2_client = None
        r2_bucket = None
        r2_public_base_url = None
        r2_path_prefix = None

        blob_token = None
        blob_upload_endpoint = None
        blob_path_prefix = None

        if storage_backend == 'r2':
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
                self.stderr.write(
                    self.style.ERROR(f"Missing R2 config in DIGIMON_IMAGE_SYNC / env: {', '.join(missing)}")
                )
                return

            r2_client = self.build_r2_client(sync_config)

        elif storage_backend == 'vercel_blob':
            blob_token = sync_config.get('BLOB_READ_WRITE_TOKEN') or os.getenv('BLOB_READ_WRITE_TOKEN')
            blob_upload_endpoint = sync_config.get('BLOB_UPLOAD_ENDPOINT', 'https://blob.vercel-storage.com')
            blob_path_prefix = sync_config.get('BLOB_PATH_PREFIX', 'cards/')

            if not blob_token:
                self.stderr.write(self.style.ERROR("Missing BLOB_READ_WRITE_TOKEN in DIGIMON_IMAGE_SYNC / env."))
                return

        else:
            self.stderr.write(self.style.ERROR(f"Unsupported storage backend: '{storage_backend}'"))
            return

        if source_type != 'github_repo':
            self.stderr.write(self.style.ERROR(f"Unsupported source type: '{source_type}'"))
            return

        branch = sync_config.get('GITHUB_BRANCH', 'main')
        github_token = sync_config.get('GITHUB_TOKEN') or os.getenv('GITHUB_TOKEN')

        try:
            files = self.fetch_all_repo_files(github_api_url, branch, github_token=github_token)
        except (ValueError, RuntimeError) as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        self.stdout.write(f"Found {len(files)} files in repo.")

        cards_with_images = set()
        if only_missing:
            cards_with_images = set(
                CardImage.objects.values_list('card__card_number', flat=True).distinct()
            )
            self.stdout.write(
                f"--only-missing: {len(cards_with_images)} cards already have at least one image "
                "and will be skipped entirely."
            )

        synced_count = 0
        skipped_count = 0

        for file_info in files:
            filename = file_info.get("name")
            raw_url = file_info.get("download_url")

            if file_info.get("type") != "file" or not raw_url:
                continue

            # Sample/preview images are watermarked placeholders, not real
            # card art. The old (buggy) suffix-stripping regex accidentally
            # filtered these out because it left "-Sample" glued onto the
            # card number, causing a lookup miss. Now that lookup is fixed,
            # exclude them explicitly instead of relying on that accident.
            if 'sample' in filename.lower():
                skipped_count += 1
                continue

            card_number, variant_type = self.parse_card_number(filename, alt_indicators)

            card = DigimonCard.objects.filter(card_number__iexact=card_number).first()
            if not card:
                self.stdout.write(
                    self.style.WARNING(f"Skipping {filename}: Card '{card_number}' not found in DB.")
                )
                continue

            if only_missing and card.card_number in cards_with_images:
                skipped_count += 1
                continue

            existing_image = CardImage.objects.filter(card=card, source_filename=filename).first()
            if existing_image and not force:
                skipped_count += 1
                continue

            self.stdout.write(f"Syncing {filename} ({variant_type}) for card {card_number}...")

            img_res = requests.get(raw_url)
            if img_res.status_code != 200:
                self.stderr.write(self.style.ERROR(f"Failed to download {raw_url}"))
                continue

            image_bytes = img_res.content
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or "image/png"

            public_url = None

            if storage_backend == 'r2':
                key = f"{r2_path_prefix.strip('/')}/{filename}"
                try:
                    public_url = self.upload_to_r2(
                        r2_client, r2_bucket, key, image_bytes, mime_type, r2_public_base_url
                    )
                except ClientError as e:
                    self.stderr.write(self.style.ERROR(f"R2 upload failed for {filename}: {e}"))
                    continue

            elif storage_backend == 'vercel_blob':
                public_url = self.upload_to_vercel_blob(
                    image_bytes, filename, mime_type, blob_token, blob_upload_endpoint, blob_path_prefix
                )
                if public_url is None:
                    continue

            if not public_url:
                self.stderr.write(self.style.ERROR(f"No public URL returned for {filename}, skipping."))
                continue

            has_primary = card.images.filter(is_primary=True).exists()
            is_primary = (not has_primary) and (variant_type == 'standard')

            CardImage.objects.update_or_create(
                card=card,
                source_filename=filename,
                defaults={
                    'image_url': public_url,
                    'variant_type': variant_type,
                    'is_primary': is_primary,
                    'storage_backend': storage_backend,
                },
            )

            synced_count += 1
            self.stdout.write(self.style.SUCCESS(f"Synced {filename} -> {public_url}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nSync complete! Synced: {synced_count}, Skipped: {skipped_count}")
        )