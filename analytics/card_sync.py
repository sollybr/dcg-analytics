import logging
import math
import time
import requests
import re

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
    """
    Extract (expansion_code, expansion_name) from raw card data.
    Fixes cases where notes don't contain colons (e.g., 'SPECIAL BOOSTER VER.2.0 [BT18-19]').
    """
    code = get_expansion(card)
    notes = str(card.get("notes", "")).strip()
    name = ""

    if notes:
        # Strip code prefix if formatted like "BT17: BOOSTER SECRET CRISIS [BT17]"
        if ":" in notes:
            parts = notes.split(":", 1)
            name = parts[1].strip()
        else:
            name = notes.strip()

    # Fallback to expansion code if no descriptive set name is available
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


def sync_expansions(raw_cards=None, stdout_writer=None, mode="distinct"):
    """
    Synchronizes card expansions into the CardExpansion table.
    
    :param mode: 'distinct' (creates individual rows per code+name pair, recommended)
                 'combine' (merges multiple names into a single row per code)
    """
    def log_msg(msg: str):
        logger.info(msg)
        if stdout_writer:
            stdout_writer(msg)

    if raw_cards is None:
        raw_cards = fetch_remote_cards()

    log_msg(f"Synchronizing card expansions (mode: {mode})...")

    if mode == "combine":
        # Group unique names by code
        code_to_names = {}
        for raw_card in raw_cards:
            if not isinstance(raw_card, dict) or not is_valid_card(raw_card):
                continue

            code, name = extract_expansion_info(raw_card)
            if not code:
                continue

            if code not in code_to_names:
                code_to_names[code] = set()
            if name and name != code:
                code_to_names[code].add(name)

        expansion_map = {
            code: " / ".join(sorted(names)) if names else code
            for code, names in code_to_names.items()
        }

        existing = {
            exp.expansion_code: exp
            for exp in CardExpansion.objects.filter(expansion_code__in=expansion_map.keys())
        }

        to_create = []
        to_update = []

        for code, combined_name in expansion_map.items():
            if code in existing:
                exp_obj = existing[code]
                if exp_obj.expansion_name != combined_name:
                    exp_obj.expansion_name = combined_name
                    to_update.append(exp_obj)
            else:
                to_create.append(
                    CardExpansion(expansion_code=code, expansion_name=combined_name)
                )

        if to_create:
            CardExpansion.objects.bulk_create(to_create)
        if to_update:
            CardExpansion.objects.bulk_update(to_update, fields=["expansion_name"])

        log_msg(f"Expansions synchronized: {len(to_create)} created, {len(to_update)} updated.")
        return {"created": len(to_create), "updated": len(to_update)}

    else:  # mode == 'distinct'
        # Collect distinct (code, name) tuples
        unique_pairs = set()

        for raw_card in raw_cards:
            if not isinstance(raw_card, dict) or not is_valid_card(raw_card):
                continue

            code, name = extract_expansion_info(raw_card)
            if code:
                unique_pairs.add((code, name))

        if not unique_pairs:
            log_msg("No expansions found to synchronize.")
            return {"created": 0, "updated": 0}

        existing_pairs = set(
            CardExpansion.objects.values_list("expansion_code", "expansion_name")
        )

        to_create = [
            CardExpansion(expansion_code=code, expansion_name=name)
            for (code, name) in unique_pairs
            if (code, name) not in existing_pairs
        ]

        if to_create:
            CardExpansion.objects.bulk_create(to_create)

        log_msg(f"Expansions synchronized: {len(to_create)} created.")
        return {"created": len(to_create), "updated": 0}


def extract_expansion_code_from_card(card_data: dict) -> str:
    """
    Extracts the expansion code. Prioritizes note/set combined codes (e.g., BT18-19)
    over standard card number prefixes (e.g., BT19).
    """
    notes = card_data.get("notes", "") or card_data.get("set_name", "")
    range_match = re.search(r'\b([A-Z]{1,3}\d{1,2}-\d{1,2})\b', notes)
    if range_match:
        return range_match.group(1)  # e.g. "BT18-19" or "BT19-20"

    card_num = card_data.get("cardNumber", "") or card_data.get("card_number", "")
    if "-" in card_num:
        return card_num.split("-")[0]

    return ""


def sync_cards(stdout_writer=None, sync_expansions_table=True, expansion_mode="distinct"):
    """
    Synchronize remote GitHub card list (and expansions) into database.
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
        expansions_res = sync_expansions(
            raw_cards=raw_cards,
            stdout_writer=stdout_writer,
            mode=expansion_mode,
        )

    # Deduplicate & Sanitize in memory
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

    # Check existing cards
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

        # Override the naive prefix-derived expansion with the range-aware
        # extraction so BT18-19 / BT19-20 combined releases don't collapse
        # into plain BT19.
        defaults["expansion"] = extract_expansion_code_from_card(raw_card) or defaults.get("expansion", "")

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

    # Bulk Upsert
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
