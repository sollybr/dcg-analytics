import logging
import math
import time
import requests

from django.core.cache import cache
from .models import DigimonCard, CardExpansion

logger = logging.getLogger(__name__)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "TakaOtaku/Digimon-Card-App/"
    "main/src/assets/cardlists/DigimonCards.json"
)

REQUEST_TIMEOUT = 25


def format_duration(seconds: float) -> str:
    """Format seconds into readable string (e.g. '1m 15s' or '2.4s')."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem_seconds = int(seconds % 60)
    return f"{minutes}m {rem_seconds}s"


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


def extract_expansion_info(card):
    """Extract (expansion_code, expansion_name) from raw card data."""
    code = get_expansion(card)
    notes = str(card.get("notes", "")).strip()
    name = ""

    if notes and ":" in notes:
        parts = notes.split(":", 1)
        name = parts[1].strip()

    # Fallback to code if no human-readable name is defined
    if not name:
        name = code

    return code, name


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


def sync_expansions(raw_cards=None, stdout_writer=None):
    """
    Synchronizes unique card expansions into the CardExpansion table.
    """
    def log_msg(msg: str):
        logger.info(msg)
        if stdout_writer:
            stdout_writer(msg)

    if raw_cards is None:
        raw_cards = fetch_remote_cards()

    log_msg("Synchronizing card expansions...")

    expansion_map = {}  # expansion_code -> expansion_name

    for raw_card in raw_cards:
        if not isinstance(raw_card, dict) or not is_valid_card(raw_card):
            continue

        code, name = extract_expansion_info(raw_card)
        if not code:
            continue

        # Register code or update if we found a descriptive name vs fallback
        if code not in expansion_map or (expansion_map[code] == code and name != code):
            expansion_map[code] = name

    if not expansion_map:
        log_msg("No expansions found to synchronize.")
        return {"created": 0, "updated": 0}

    # Fetch existing expansions from DB
    existing_expansions = {
        exp.expansion_code: exp
        for exp in CardExpansion.objects.filter(expansion_code__in=expansion_map.keys())
    }

    to_create = []
    to_update = []

    for code, name in expansion_map.items():
        if code in existing_expansions:
            exp_obj = existing_expansions[code]
            if exp_obj.expansion_name != name and name != code:
                exp_obj.expansion_name = name
                to_update.append(exp_obj)
        else:
            to_create.append(
                CardExpansion(
                    expansion_code=code,
                    expansion_name=name,
                )
            )

    if to_create:
        CardExpansion.objects.bulk_create(to_create)
    if to_update:
        CardExpansion.objects.bulk_update(to_update, fields=["expansion_name"])

    log_msg(f"Expansions synchronized: {len(to_create)} created, {len(to_update)} updated.")
    return {"created": len(to_create), "updated": len(to_update)}


def sync_cards(stdout_writer=None, sync_expansions_table=True):
    """
    Synchronize remote GitHub card list (and expansions) into database.
    
    :param stdout_writer: Optional stdout print function
    :param sync_expansions_table: If True, also syncs CardExpansion table
    """
    start_time = time.perf_counter()

    def log_msg(msg: str):
        logger.info(msg)
        if stdout_writer:
            stdout_writer(msg)

    log_msg("Attempting Digimon card database refresh from GitHub...")

    try:
        raw_cards = fetch_remote_cards()
        fetch_duration = time.perf_counter() - start_time
        log_msg(f"Fetched {len(raw_cards)} raw records in {format_duration(fetch_duration)}.")
    except Exception as e:
        logger.exception("Could not refresh Digimon cards from GitHub.")
        raise RuntimeError(f"Fetch failed: {str(e)}")

    # Sync expansions first using the fetched raw_cards payload
    expansions_res = {"created": 0, "updated": 0}
    if sync_expansions_table:
        expansions_res = sync_expansions(raw_cards=raw_cards, stdout_writer=stdout_writer)

    # 1. Deduplicate & Sanitize in memory
    card_map = {}
    skipped = 0

    for raw_card in raw_cards:
        if not isinstance(raw_card, dict) or not is_valid_card(raw_card):
            skipped += 1
            continue

        card_number = str(raw_card.get("cardNumber", "")).strip()
        card_map[card_number] = raw_card

    if not card_map:
        total_time = time.perf_counter() - start_time
        log_msg(f"No valid cards found. Total time: {format_duration(total_time)}")
        return {
            "status": "success",
            "created": 0,
            "updated": 0,
            "skipped": skipped,
            "expansions_created": expansions_res["created"],
            "expansions_updated": expansions_res["updated"],
            "elapsed_seconds": round(total_time, 2),
            "elapsed_formatted": format_duration(total_time),
        }

    # 2. Check existing cards to compute created/updated counts
    existing_numbers = set(
        DigimonCard.objects.filter(card_number__in=card_map.keys()).values_list(
            "card_number", flat=True
        )
    )

    created = 0
    updated = 0
    card_objects = []

    for card_number, raw_card in card_map.items():
        defaults = card_defaults(raw_card)
        card_objects.append(
            DigimonCard(
                card_number=card_number,
                **defaults,
            )
        )
        if card_number in existing_numbers:
            updated += 1
        else:
            created += 1

    # 3. Batched Bulk Upsert with dynamic ETA calculation
    update_fields = [
        "name", "rarity", "card_type", "color",
        "card_level", "play_cost", "expansion", "subtype", "data",
    ]

    batch_size = 500
    total_objects = len(card_objects)
    total_batches = math.ceil(total_objects / batch_size)
    db_start_time = time.perf_counter()

    for i in range(0, total_objects, batch_size):
        batch = card_objects[i : i + batch_size]
        current_batch_num = (i // batch_size) + 1

        DigimonCard.objects.bulk_create(
            batch,
            update_conflicts=True,
            unique_fields=["card_number"],
            update_fields=update_fields,
        )

        # Time metrics calculation
        elapsed_so_far = time.perf_counter() - start_time
        db_elapsed = time.perf_counter() - db_start_time
        avg_time_per_batch = db_elapsed / current_batch_num
        remaining_batches = total_batches - current_batch_num
        eta_seconds = remaining_batches * avg_time_per_batch

        processed_count = min(i + batch_size, total_objects)
        percent = int((processed_count / total_objects) * 100)

        log_msg(
            f"[{percent}%] Batch {current_batch_num}/{total_batches} synced "
            f"({processed_count}/{total_objects} cards) | "
            f"Elapsed: {format_duration(elapsed_so_far)} | "
            f"ETA: {format_duration(eta_seconds)}"
        )

    # Invalidate cache
    cache.clear()

    total_time = time.perf_counter() - start_time
    log_msg(
        f"Refresh complete in {format_duration(total_time)}: "
        f"{created} created, {updated} updated, {skipped} skipped."
    )

    return {
        "status": "success",
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "expansions_created": expansions_res["created"],
        "expansions_updated": expansions_res["updated"],
        "elapsed_seconds": round(total_time, 2),
        "elapsed_formatted": format_duration(total_time),
    }