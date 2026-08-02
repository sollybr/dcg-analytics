from collections import Counter

from django.core.cache import cache
from django.http import JsonResponse

from .card_sync import maybe_refresh_cards
from .models import DigimonCard


CACHE_TIMEOUT = 60 * 60 * 6


def analytics_data(request):
    """
    Return analytics calculated from SQLite.

    GitHub synchronization is triggered in the background
    when necessary. The HTTP request never waits for GitHub.
    """

    # This only schedules a background operation if the
    # refresh interval has elapsed.
    #
    # It does NOT make the request wait for the network.
    maybe_refresh_cards()

    cache_key = (
        f"analytics_data:{request.get_full_path()}"
    )

    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return JsonResponse(cached_data)

    cards = DigimonCard.objects.all()

    type_counter = Counter()
    name_counter = Counter()
    single_color_counter = Counter()
    multicolor_counter = Counter()
    expansion_counter = Counter()
    sec_color_counter = Counter()
    subtype_counter = Counter()

    for card in cards:
        # -----------------------------------------------------
        # CARD TYPE
        # -----------------------------------------------------

        card_type = card.card_type

        if card_type and card_type != "-":
            type_counter[card_type] += 1

        # -----------------------------------------------------
        # NAME
        # -----------------------------------------------------

        name = card.name or "Unknown"
        name_counter[name] += 1

        # -----------------------------------------------------
        # COLOR
        # -----------------------------------------------------

        color = card.color or "Unknown"

        if "/" in color:
            multicolor_counter[color] += 1
        else:
            single_color_counter[color] += 1

        # -----------------------------------------------------
        # EXPANSION
        # -----------------------------------------------------

        expansion = card.expansion or "Other"
        expansion_counter[expansion] += 1

        # -----------------------------------------------------
        # SEC COLOR
        # -----------------------------------------------------

        rarity = str(card.rarity).upper()

        if "SEC" in rarity:
            if "/" in color:
                for value in color.split("/"):
                    cleaned = value.strip()

                    if cleaned:
                        sec_color_counter[cleaned] += 1
            else:
                sec_color_counter[color] += 1

        # -----------------------------------------------------
        # SUBTYPE
        # -----------------------------------------------------

        raw_subtype = card.subtype

        if raw_subtype:
            subtypes = [
                value.strip()
                for value in raw_subtype.split("/")
                if value.strip()
                and value.strip() != "-"
            ]

            for subtype in subtypes:
                subtype_counter[subtype] += 1

    top_names = name_counter.most_common(15)

    top_multicolors = (
        multicolor_counter.most_common(10)
    )

    top_subtypes = (
        subtype_counter.most_common(20)
    )

    sorted_expansions = sorted(
        expansion_counter.items(),
        key=lambda item: item[0],
    )

    data = {
        "total_cards": cards.count(),

        "type_labels": list(
            type_counter.keys()
        ),
        "type_data": list(
            type_counter.values()
        ),

        "name_labels": [
            name
            for name, _ in top_names
        ],
        "name_data": [
            count
            for _, count in top_names
        ],

        "single_color_labels": list(
            single_color_counter.keys()
        ),
        "single_color_data": list(
            single_color_counter.values()
        ),

        "multicolor_labels": [
            color
            for color, _ in top_multicolors
        ],
        "multicolor_data": [
            count
            for _, count in top_multicolors
        ],

        "expansion_labels": [
            expansion
            for expansion, _ in sorted_expansions
        ],
        "expansion_data": [
            count
            for _, count in sorted_expansions
        ],

        "sec_color_labels": list(
            sec_color_counter.keys()
        ),
        "sec_color_data": list(
            sec_color_counter.values()
        ),

        "subtype_labels": [
            subtype
            for subtype, _ in top_subtypes
        ],
        "subtype_data": [
            count
            for _, count in top_subtypes
        ],
    }

    cache.set(
        cache_key,
        data,
        CACHE_TIMEOUT,
    )

    return JsonResponse(data)


def cards_by_name(request):
    """
    Return all cards with a given English name.

    Example:
        /api/cards/?name=Agumon
    """

    maybe_refresh_cards()

    name = request.GET.get(
        "name",
        "",
    ).strip()

    if not name:
        return JsonResponse(
            {
                "error": "Missing name parameter."
            },
            status=400,
        )

    cache_key = (
        f"cards_by_name:{name.casefold()}"
    )

    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return JsonResponse(cached_data)

    cards = (
        DigimonCard.objects
        .filter(name__iexact=name)
        .order_by("card_number")
    )

    data = {
        "name": name,
        "count": cards.count(),
        "cards": [
            card.data
            for card in cards
        ],
    }

    cache.set(
        cache_key,
        data,
        CACHE_TIMEOUT,
    )

    return JsonResponse(data)