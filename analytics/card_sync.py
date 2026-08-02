import logging
from threading import Thread

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

# Try GitHub at most once every 6 hours.
REFRESH_INTERVAL = 60 * 60 * 6

# Never allow the GitHub request itself to hang for a long time.
REQUEST_TIMEOUT = 10

REFRESH_TIMESTAMP_KEY = "digimon_cards:last_refresh_attempt"
REFRESH_LOCK_KEY = "digimon_cards:refresh_lock"


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
        name = str(
            name_obj.get("english", "")
        ).strip()
    else:
        name = str(name_obj).strip()

    if (
        not name
        or name.startswith("[[:Category:")
        or name == "-"
    ):
        return False

    rarity = str(
        card.get("rarity", "")
    ).strip()

    if not rarity or rarity == "-":
        return False

    card_number = str(
        card.get("cardNumber", "")
    ).strip()

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
    card_number = str(
        card.get("cardNumber", "")
    ).strip()

    if "-" in card_number:
        return card_number.split("-")[0].strip()

    notes = card.get("notes", "")

    if notes and ":" in notes:
        return str(
            notes.split(":")[0]
        ).strip()

    return "Other"


def card_defaults(card):
    name_obj = card.get("name", {})

    if isinstance(name_obj, dict):
        name = str(
            name_obj.get("english", "")
        ).strip()
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
    """
    Attempt to download the upstream card list.

    Returns:
        list: cards on success

    Raises:
        requests.RequestException: network-related failure
        ValueError: invalid JSON / unexpected response
    """

    response = requests.get(
        DATA_URL,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError(
            "GitHub card data is not a JSON array."
        )

    return data


def sync_cards():
    """
    Synchronize the remote card list into SQLite.

    Existing cards are updated.
    New cards are inserted.

    Nothing is deleted from SQLite. This is intentional:
    a temporary omission from upstream shouldn't wipe
    locally known cards.
    """

    logger.info(
        "Attempting Digimon card database refresh from GitHub."
    )

    try:
        raw_cards = fetch_remote_cards()
    except Exception:
        logger.exception(
            "Could not refresh Digimon cards from GitHub. "
            "Keeping existing SQLite data."
        )
        return False

    created = 0
    updated = 0
    skipped = 0

    with transaction.atomic():
        for raw_card in raw_cards:
            if not isinstance(raw_card, dict):
                skipped += 1
                continue

            if not is_valid_card(raw_card):
                skipped += 1
                continue

            card_number = str(
                raw_card.get("cardNumber", "")
            ).strip()

            defaults = card_defaults(raw_card)

            _, was_created = (
                DigimonCard.objects.update_or_create(
                    card_number=card_number,
                    defaults=defaults,
                )
            )

            if was_created:
                created += 1
            else:
                updated += 1

    # The analytics response is based on SQLite, so it is
    # no longer valid after the database changes.
    cache.clear()

    logger.info(
        "Digimon card refresh complete: "
        "%d created, %d updated, %d skipped.",
        created,
        updated,
        skipped,
    )

    return True


def _background_sync():
    """
    Wrapper for the daemon thread.
    """

    try:
        sync_cards()
    finally:
        # Allow a later request to schedule another refresh.
        cache.delete(REFRESH_LOCK_KEY)


def maybe_refresh_cards():
    """
    Schedule a background refresh if the refresh interval
    has elapsed.

    This function NEVER waits for GitHub.
    """

    if cache.get(REFRESH_TIMESTAMP_KEY):
        return

    # Only one request is allowed to schedule a refresh.
    #
    # cache.add() is atomic for Django cache backends that
    # support atomic add semantics.
    acquired = cache.add(
        REFRESH_LOCK_KEY,
        True,
        REFRESH_INTERVAL,
    )

    if not acquired:
        return

    # Record the attempt time before starting the thread.
    #
    # This prevents every incoming request from spawning
    # another thread while the network request is running.
    cache.set(
        REFRESH_TIMESTAMP_KEY,
        True,
        REFRESH_INTERVAL,
    )

    thread = Thread(
        target=_background_sync,
        daemon=True,
        name="digimon-card-sync",
    )

    thread.start()
    