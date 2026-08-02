import logging
import requests

from django.core.cache import cache
from django.db import transaction

from .models import DigimonCard

logger = logging.getLogger(__name__)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "TakaOtaku/Digimon-Card-App/"
    "main/src/assets/cardlists/DigimonCards.json"
)

# Keep timeout under Vercel serverless limit (default 10s-60s)
REQUEST_TIMEOUT = 25


def clean_string(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return "/".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    return str(value).strip()


def is_valid_card(card):
    name_obj = card.get("name", {})

    if isinstance(name_obj, dict):
        name = str(name_obj.get("english", "")).strip()
    else:
        name = str(name_obj).strip()

    if (
        not name
        or name.startswith("[[:Category:")
        or name == "-"
    ):
        return False

    rarity = str(card.get("rarity", "")).strip()
    if not rarity or rarity == "-":
        return False

    card_number = str(card.get("cardNumber", "")).strip()
    if not card_number or card_number == "-":
        return False

    return True


def sanitize_card(card):
    """
    Make a copy and normalize problematic text without
    modifying the object returned by requests.
    """
    sanitized = dict(card)
    text_fields = [
        "effect",
        "digivolveEffect",
        "securityEffect",
        "aceEffect",
        "specialDigivolve",
        "assembly",
    ]

    for field in text_fields:
        value = sanitized.get(field)
        if isinstance(value, str):
            sanitized[field] = (
                value
                .replace("\u00a0", " ")
                .replace("\uff1c", "<")
                .replace("\uff1e", ">")
            )

    return sanitized


def get_expansion(card):
    card_number = str(card.get("cardNumber", "")).strip()

    if "-" in card_number:
        return card_number.split("-")[0].strip()

    notes = card.get("notes", "")

    if notes and ":" in notes:
        return str(notes.split(":")[0]).strip()

    return "Other"


def card_defaults(card):
    name_obj = card.get("name", {})

    if isinstance(name_obj, dict):
        name = str(name_obj.get("english", "")).strip()
    else:
        name = str(name_obj).strip()

    return {
        "name": name,
        "rarity": clean_string(card.get("rarity")),
        "card_type": clean_string(card.get("cardType")),
        "color": clean_string(card.get("color")),
        "card_level": clean_string(card.get("cardLv")),
        "play_cost": clean_string(card.get("playCost")),
        "expansion": get_expansion(card),
        "subtype": clean_string(card.get("type")),
        "data": sanitize_card(card),
    }


def fetch_remote_cards():
    response = requests.get(
        DATA_URL,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("GitHub card data is not a JSON array.")

    return data


def sync_cards():
    """
    Synchronize remote GitHub card list into database.
    Updates existing records, inserts new ones.
    """
    logger.info("Attempting Digimon card database refresh from GitHub.")

    try:
        raw_cards = fetch_remote_cards()
    except Exception as e:
        logger.exception("Could not refresh Digimon cards from GitHub.")
        raise RuntimeError(f"Fetch failed: {str(e)}")

    created = 0
    updated = 0
    skipped = 0

    with transaction.atomic():
        for raw_card in raw_cards:
            if not isinstance(raw_card, dict) or not is_valid_card(raw_card):
                skipped += 1
                continue

            card_number = str(raw_card.get("cardNumber", "")).strip()
            defaults = card_defaults(raw_card)

            _, was_created = DigimonCard.objects.update_or_create(
                card_number=card_number,
                defaults=defaults,
            )

            if was_created:
                created += 1
            else:
                updated += 1

    # Invalidate cache after modification
    cache.clear()

    logger.info(
        "Digimon card refresh complete: %d created, %d updated, %d skipped.",
        created,
        updated,
        skipped,
    )

    return {
        "status": "success",
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }