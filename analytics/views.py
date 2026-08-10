# import os
import re
from collections import Counter

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings

from .card_sync import sync_cards
from .models import DigimonCard

from .statistics.distributions import conditional_distribution
from .statistics.schema import (
    get_analytics_fields,
    get_categorical_fields,
)
from .statistics.associations import cramers_v

def natural_sort_key(item):
    """
    Sorts strings containing numbers logically (e.g., BT1, BT2, BT10).
    """
    expansion_name = item[0]
    return [
        int(text) if text.isdigit() else text.lower() 
        for text in re.split(r'(\d+)', expansion_name)
    ]


def get_expansion_type(card_number):
    if not card_number:
        return "Other"
    match = re.match(r'^([A-Z]+)', card_number)
    return match.group(1) if match else "Other"


def sync_cards_view(request):
    expected_token = settings.CRON_SECRET # os.environ.get("CRON_SECRET") or os.environ.get("CARD_SYNC_TOKEN")

    # if not expected_token:
    #     return JsonResponse(
    #         {"error": "Server cron secret is not configured."},
    #         status=500
    #     )

    auth_header = request.headers.get("Authorization", "")
    token_from_header = ""
    if auth_header.startswith("Bearer "):
        token_from_header = auth_header.split("Bearer ")[1].strip()

    supplied_token = (
        token_from_header or 
        request.headers.get("X-Card-Sync-Token") or 
        request.GET.get("token")
    )

    if supplied_token != expected_token:
        return JsonResponse(
            {"error": "Unauthorized request."},
            status=403
        )

    try:
        result = sync_cards()
        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


CACHE_TIMEOUT = 60 * 60 * 6


def analytics_data(request):
    cards = DigimonCard.objects.all()

    type_counter = Counter()
    name_counter = Counter()
    single_color_counter = Counter()
    multicolor_counter = Counter()
    expansion_counter = Counter()
    sec_color_counter = Counter()
    subtype_counter = Counter()
    expansion_types = {}

    for card in cards:
        card_type = card.card_type

        if card_type and card_type != "-":
            type_counter[card_type] += 1

        name = card.name or "Unknown"
        name_counter[name] += 1

        color = card.color or "Unknown"

        if "/" in color:
            multicolor_counter[color] += 1
        else:
            single_color_counter[color] += 1

        expansion = card.expansion or "Other"
        expansion_counter[expansion] += 1

        # Use helper function to map the expansion type
        expansion_type = get_expansion_type(card.card_number)
        expansion_types[expansion] = expansion_type

        rarity = str(card.rarity).upper()

        if "SEC" in rarity:
            if "/" in color:
                for value in color.split("/"):
                    cleaned = value.strip()

                    if cleaned:
                        sec_color_counter[cleaned] += 1
            else:
                sec_color_counter[color] += 1

        raw_subtype = card.subtype

        if raw_subtype:
            subtypes = [
                value.strip()
                for value in raw_subtype.split("/")
                if value.strip() and value.strip() != "-"
            ]

            for subtype in subtypes:
                subtype_counter[subtype] += 1

    top_names = name_counter.most_common(15)
    top_multicolors = multicolor_counter.most_common(10)
    top_subtypes = subtype_counter.most_common(20)

    sorted_expansions = sorted(
        expansion_counter.items(),
        key=natural_sort_key,
    )

    expansion_labels = [
        expansion for expansion, _ in sorted_expansions
    ]

    expansion_data = [
        count for _, count in sorted_expansions
    ]

    data = {
        "total_cards": cards.count(),

        "type_labels": list(type_counter.keys()),
        "type_data": list(type_counter.values()),

        "name_labels": [
            name for name, _ in top_names
        ],
        "name_data": [
            count for _, count in top_names
        ],

        "single_color_labels": list(
            single_color_counter.keys()
        ),
        "single_color_data": list(
            single_color_counter.values()
        ),

        "multicolor_labels": [
            color for color, _ in top_multicolors
        ],
        "multicolor_data": [
            count for _, count in top_multicolors
        ],

        "expansion_labels": expansion_labels,
        "expansion_data": expansion_data,

        # Corrected Key Name for React mapping
        "expansion_types": [
            expansion_types.get(expansion, "Other")
            for expansion in expansion_labels
        ],

        "sec_color_labels": list(
            sec_color_counter.keys()
        ),
        "sec_color_data": list(
            sec_color_counter.values()
        ),

        "subtype_labels": [
            subtype for subtype, _ in top_subtypes
        ],
        "subtype_data": [
            count for _, count in top_subtypes
        ],
    }

    return JsonResponse(data)
    

def cards_by_name(request):
    """
    Return all cards with a given English name.
    """
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


@require_GET
def statistics_schema(request):
    return JsonResponse({
        "fields": get_analytics_fields(),
        "categorical_fields": list(
            get_categorical_fields().keys()
        ),
    })


@require_GET
def statistics_distribution(request):
    given_field = request.GET.get("given")
    given_value = request.GET.get("value")
    target_field = request.GET.get("target")

    categorical_fields = get_categorical_fields()

    if given_field not in categorical_fields:
        return JsonResponse(
            {"error": f"Invalid given field: {given_field}"},
            status=400,
        )

    if target_field not in categorical_fields:
        return JsonResponse(
            {"error": f"Invalid target field: {target_field}"},
            status=400,
        )

    if not given_value:
        return JsonResponse(
            {"error": "Missing 'value' parameter."},
            status=400,
        )

    cards = DigimonCard.objects.all()

    result = conditional_distribution(
        DigimonCard,
        given_field,
        target_field,
        given_value,
    )

    return JsonResponse({
        "given": {
            "field": given_field,
            "value": given_value,
        },
        "target": {
            "field": target_field,
        },
        "distribution": result,
    })


@require_GET
def statistics_association(request):
    first_field = request.GET.get("first")
    second_field = request.GET.get("second")

    categorical_fields = get_categorical_fields()

    if first_field not in categorical_fields:
        return JsonResponse(
            {"error": f"Invalid field: {first_field}"},
            status=400,
        )

    if second_field not in categorical_fields:
        return JsonResponse(
            {"error": f"Invalid field: {second_field}"},
            status=400,
        )

    rows = list(
        DigimonCard.objects.values(
            first_field,
            second_field,
        )
    )

    value = cramers_v(
        rows,
        first_field,
        second_field,
    )

    return JsonResponse({
        "fields": {
            "first": first_field,
            "second": second_field,
        },
        "cramers_v": value,
    })


from django.core.paginator import Paginator

def cards_by_type(request):
    """
    Return paginated cards matching a specific subtype.
    Example: /api/cards-by-type/?type=Vaccine&page=1
    """
    card_type = request.GET.get("type", "").strip()
    page_number = int(request.GET.get("page", 1))

    if not card_type:
        return JsonResponse({"error": "Missing type parameter."}, status=400)

    cards = DigimonCard.objects.filter(subtype__icontains=card_type).order_by("card_number")

    # Paginate by 25 cards per request
    paginator = Paginator(cards, 25)
    page_obj = paginator.get_page(page_number)

    data = {
        "type": card_type,
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
        "cards": [card.data for card in page_obj.object_list],
    }
    
    return JsonResponse(data)
