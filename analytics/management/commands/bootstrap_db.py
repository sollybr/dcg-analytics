import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

from analytics.models import DigimonCard, CardImage
from analytics.card_sync import sync_cards  # Import your sync function


class Command(BaseCommand):
    help = 'Automatically handles migrations, fixes table desyncs, and syncs card + image data'

    def _table_missing(self, model):
        """Return True if the model's table isn't physically present in the DB."""
        table_name = model._meta.db_table
        with connection.cursor() as cursor:
            return table_name not in connection.introspection.table_names(cursor)

    def handle(self, *args, **options):
        # -------------------------------------------------------------------
        # 1. Schema sanity check
        # -------------------------------------------------------------------
        self.stdout.write(self.style.WARNING("Checking database schema state..."))

        # Models whose tables we sanity-check before migrating.
        # Add future models here as the schema grows.
        models_to_check = [DigimonCard, CardImage]

        try:
            missing = [m for m in models_to_check if self._table_missing(m)]

            # Only nuke migration history if EVERY tracked table is missing —
            # that's the real "DB wiped but django_migrations still thinks
            # it ran" scenario. If just some tables are missing (e.g. you
            # added a new model), that's a normal pending migration —
            # `migrate` handles it correctly on its own, so leave it alone.
            if missing and len(missing) == len(models_to_check):
                app_label = models_to_check[0]._meta.app_label
                self.stdout.write(
                    self.style.WARNING(
                        f"All tracked tables for '{app_label}' are missing. "
                        "Cleaning up stale migration history..."
                    )
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM django_migrations WHERE app = %s;",
                        [app_label],
                    )
                self.stdout.write(self.style.SUCCESS("Stale migration history cleared."))
            elif missing:
                names = ", ".join(m._meta.db_table for m in missing)
                self.stdout.write(
                    f"Some tables not yet created ({names}) — "
                    "letting migrate apply pending migrations normally."
                )
        except Exception:
            # Safe fallback if tables (like django_migrations itself) don't exist
            # yet on a brand-new database.
            pass

        # -------------------------------------------------------------------
        # 2. Migrate
        # -------------------------------------------------------------------
        self.stdout.write(self.style.WARNING("Running database migrations..."))
        call_command('migrate')
        self.stdout.write(self.style.SUCCESS("Migrations applied successfully!"))

        # -------------------------------------------------------------------
        # 3. Sync card data (always runs, regardless of image config)
        # -------------------------------------------------------------------
        self.stdout.write(self.style.WARNING("Syncing card data..."))
        try:
            result = sync_cards(stdout_writer=self.stdout.write)
            elapsed = result.get("elapsed_formatted", "")
            created = result.get("created", 0)
            updated = result.get("updated", 0)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cards synchronized and database populated successfully in {elapsed}! "
                    f"({created} created, {updated} updated)"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during card sync: {e}"))
            # Image sync depends on cards existing, so bail out here.
            return

        # -------------------------------------------------------------------
        # 4. Sync card images (optional — only if Vercel Blob is configured)
        # -------------------------------------------------------------------
        sync_config = getattr(settings, 'DIGIMON_IMAGE_SYNC', {})
        blob_token = sync_config.get('BLOB_READ_WRITE_TOKEN') or os.getenv('BLOB_READ_WRITE_TOKEN')

        if not blob_token:
            self.stdout.write(
                self.style.WARNING(
                    "No BLOB_READ_WRITE_TOKEN found in DIGIMON_IMAGE_SYNC/env — skipping image sync. "
                    "The app will run fine without images; card.images will just be empty."
                )
            )
            return

        self.stdout.write(self.style.WARNING("Syncing card images..."))
        try:
            call_command('sync_card_images')
            self.stdout.write(self.style.SUCCESS("Image sync complete!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during image sync: {e}"))