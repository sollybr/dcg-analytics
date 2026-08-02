import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache

from analytics.models import DigimonCard


class Command(BaseCommand):
    help = 'Import Digimon cards from a DigimonCards.json file into SQLite.'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to DigimonCards.json',
        )

    def handle(self, *args, **options):
        json_path = Path(options['json_file'])

        if not json_path.exists():
            raise CommandError(
                f'JSON file does not exist: {json_path}'
            )

        try:
            with json_path.open(
                'r',
                encoding='utf-8',
            ) as file:
                cards = json.load(file)
        except json.JSONDecodeError as exc:
            raise CommandError(
                f'Invalid JSON: {exc}'
            ) from exc

        if not isinstance(cards, list):
            raise CommandError(
                'Expected the JSON root to be an array of cards.'
            )

        created = 0
        updated = 0
        skipped = 0

        for card in cards:
            if not isinstance(card, dict):
                skipped += 1
                continue

            if not self.is_valid_card(card):
                skipped += 1
                continue

            card_number = str(card.get('cardNumber', '')).strip()

            name_obj = card.get('name', {})
            if isinstance(name_obj, dict):
                name = str(
                    name_obj.get('english', '')
                ).strip()
            else:
                name = str(name_obj).strip()

            color = self.clean_string(card.get('color'))
            card_type = self.clean_string(card.get('cardType'))
            rarity = self.clean_string(card.get('rarity'))
            card_level = self.clean_string(card.get('cardLv'))
            play_cost = self.clean_string(card.get('playCost'))

            expansion = self.get_expansion(card)

            subtype = self.clean_string(
                card.get('type')
            )

            defaults = {
                'name': name,
                'rarity': rarity,
                'card_type': card_type,
                'color': color,
                'card_level': card_level,
                'play_cost': play_cost,
                'expansion': expansion,
                'subtype': subtype,
                'data': self.sanitize_card(card),
            }

            _, was_created = DigimonCard.objects.update_or_create(
                card_number=card_number,
                defaults=defaults,
            )

            if was_created:
                created += 1
            else:
                updated += 1
                
        cache.clear()

        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete: '
                f'{created} created, '
                f'{updated} updated, '
                f'{skipped} skipped.'
            )
        )

    @staticmethod
    def clean_string(value):
        if value is None:
            return ''

        if isinstance(value, list):
            return '/'.join(
                str(item).strip()
                for item in value
                if str(item).strip()
            )

        return str(value).strip()

    @staticmethod
    def is_valid_card(card):
        name_obj = card.get('name', {})

        if isinstance(name_obj, dict):
            name = str(
                name_obj.get('english', '')
            ).strip()
        else:
            name = str(name_obj).strip()

        if (
            not name
            or name.startswith('[[:Category:')
            or name == '-'
        ):
            return False

        rarity = str(
            card.get('rarity', '')
        ).strip()

        if not rarity or rarity == '-':
            return False

        card_number = str(
            card.get('cardNumber', '')
        ).strip()

        if not card_number or card_number == '-':
            return False

        return True

    @staticmethod
    def sanitize_card(card):
        # Make a copy so we never mutate the object loaded by json.
        sanitized = dict(card)

        text_fields = [
            'effect',
            'digivolveEffect',
            'securityEffect',
            'aceEffect',
            'specialDigivolve',
            'assembly',
        ]

        for field in text_fields:
            value = sanitized.get(field)

            if isinstance(value, str):
                sanitized[field] = (
                    value
                    .replace('\u00a0', ' ')
                    .replace('\uff1c', '<')
                    .replace('\uff1e', '>')
                )

        return sanitized

    @staticmethod
    def get_expansion(card):
        card_number = str(
            card.get('cardNumber', '')
        ).strip()

        if '-' in card_number:
            return card_number.split('-')[0].strip()

        notes = card.get('notes', '')

        if notes and ':' in notes:
            return str(
                notes.split(':')[0]
            ).strip()

        return 'Other'