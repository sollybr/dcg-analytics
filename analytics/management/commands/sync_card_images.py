import os
import re
import mimetypes
import requests

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

    def fetch_all_repo_files(self, github_api_url, branch):
        """
        Fetch the full file list for the configured GitHub directory using
        the Git Trees API (recursive=1) instead of the Contents API.

        The Contents API silently truncates directories over ~1000 entries
        with no pagination available to get past that cap. The Trees API
        returns the complete recursive file tree in one call, which we then
        filter down to just the configured images path.
        """
        match = self.GITHUB_CONTENTS_URL_RE.search(github_api_url)
        if not match:
            raise ValueError(
                f"Could not parse owner/repo/path from GITHUB_API_URL: {github_api_url}"
            )
        owner = match.group('owner')
        repo = match.group('repo')
        images_path = match.group('path')

        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        self.stdout.write(f"Fetching full repo tree from {tree_url}...")

        tree_response = requests.get(tree_url)
        if tree_response.status_code != 200:
            raise RuntimeError(
                f"GitHub Trees API request failed ({tree_response.status_code}): {tree_response.text}"
            )

        tree_data = tree_response.json()
        if tree_data.get('truncated'):
            self.stderr.write(
                self.style.WARNING(
                    "GitHub reports this tree response was truncated (repo too large for "
                    "one recursive call). Some files past the truncation point may be missed."
                )
            )

        files = []
        prefix = images_path.rstrip('/') + '/'
        for item in tree_data.get('tree', []):
            path = item.get('path', '')
            if item.get('type') != 'blob' or not path.startswith(prefix):
                continue
            filename = path.rsplit('/', 1)[-1]
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
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

    def handle(self, *args, **options):
        sync_config = getattr(settings, 'DIGIMON_IMAGE_SYNC', {})
        force = options['force'] or sync_config.get('OVERWRITE_EXISTING', False)

        source_type = sync_config.get('SOURCE_TYPE', 'github_repo')
        github_api_url = sync_config.get('GITHUB_API_URL')

        storage_backend = sync_config.get('STORAGE_BACKEND', 'vercel_blob')
        blob_token = sync_config.get('BLOB_READ_WRITE_TOKEN') or os.getenv('BLOB_READ_WRITE_TOKEN')
        upload_endpoint = sync_config.get('BLOB_UPLOAD_ENDPOINT', 'https://blob.vercel-storage.com')
        path_prefix = sync_config.get('BLOB_PATH_PREFIX', 'cards/')
        alt_indicators = sync_config.get('ALT_ART_INDICATORS', ['_P', '_AA', '_PARALLEL', '_PROMO', '_ALT'])

        if storage_backend == 'vercel_blob' and not blob_token:
            self.stderr.write(self.style.ERROR("Missing BLOB_READ_WRITE_TOKEN in DIGIMON_IMAGE_SYNC / env."))
            return

        if storage_backend != 'vercel_blob':
            self.stderr.write(self.style.ERROR(f"Unsupported storage backend: '{storage_backend}'"))
            return

        if source_type != 'github_repo':
            self.stderr.write(self.style.ERROR(f"Unsupported source type: '{source_type}'"))
            return

        branch = sync_config.get('GITHUB_BRANCH', 'main')

        try:
            files = self.fetch_all_repo_files(github_api_url, branch)
        except (ValueError, RuntimeError) as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        self.stdout.write(f"Found {len(files)} files in repo.")

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
                continue

            public_blob_url = blob_res.json().get("url")

            has_primary = card.images.filter(is_primary=True).exists()
            is_primary = (not has_primary) and (variant_type == 'standard')

            CardImage.objects.update_or_create(
                card=card,
                source_filename=filename,
                defaults={
                    'image_url': public_blob_url,
                    'variant_type': variant_type,
                    'is_primary': is_primary,
                    'storage_backend': storage_backend,
                },
            )

            synced_count += 1
            self.stdout.write(self.style.SUCCESS(f"Synced {filename} -> {public_blob_url}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nSync complete! Synced: {synced_count}, Skipped: {skipped_count}")
        )