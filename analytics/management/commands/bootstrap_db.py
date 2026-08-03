from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

from analytics.models import DigimonCard
from analytics.card_sync import sync_cards  # Import your sync function


class Command(BaseCommand):
    help = 'Automatically handles migrations, fixes table desyncs, and syncs card data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Checking database schema state..."))

        try:
            # Check if the physical table exists in the database
            table_name = DigimonCard._meta.db_table
            with connection.cursor() as cursor:
                table_exists = table_name in connection.introspection.table_names(cursor)

            # If migration history thinks it ran, but the table is missing, clear the stale history
            if not table_exists:
                self.stdout.write(
                    self.style.WARNING(
                        f"Table '{table_name}' is missing. Cleaning up stale migration history..."
                    )
                )
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM django_migrations WHERE app = 'analytics';")
                self.stdout.write(
                    self.style.SUCCESS("Stale migration history cleared successfully.")
                )
        except Exception:
            # Safe fallback if tables (like django_migrations itself) do not exist yet on a brand-new database
            pass

        self.stdout.write(self.style.WARNING("Running database migrations..."))
        call_command('migrate')
        self.stdout.write(self.style.SUCCESS("Migrations applied successfully!"))

        self.stdout.write(self.style.WARNING("Syncing card data..."))
        try:
            # Pass self.stdout.write so progress and ETA stream live to terminal
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