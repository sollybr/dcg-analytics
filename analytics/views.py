import logging
import re
from collections import Counter

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from .card_sync import sync_cards
from .statistics.associations import cramers_v_with_diagnostics
from .models import DigimonCard, CardExpansion
from .statistics.distributions import conditional_distribution
from .statistics.schema import (
    get_analytics_fields,
    get_categorical_fields,
)

logger = logging.getLogger(__name__)

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


@require_http_methods(["POST", "GET"])
def sync_cards_view(request):
    expected_token = getattr(settings, "CRON_SECRET", None)

    if not expected_token:
        return JsonResponse(
            {"error": "Server cron secret is not configured."},
            status=500,
        )

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
            status=403,
        )

    try:
        result = sync_cards()
        return JsonResponse(result, status=200)
    except Exception:
        logger.exception("Card sync failed.")
        return JsonResponse({"error": "An internal error has occurred."}, status=500)


class CardAnalyticsEngine:
    """
    Encapsulates metric generation so they can be toggled on or off
    dynamically based on API request headers.
    """
    def __init__(self, cards):
        self.cards = cards

    def get_types(self):
        counter = Counter(
            c.card_type for c in self.cards
            if c.card_type and c.card_type != "-"
        )
        return {
            "type_labels": list(counter.keys()),
            "type_data": list(counter.values()),
        }

    def get_names(self, limit=15):
        counter = Counter(c.name or "Unknown" for c in self.cards)
        top_names = counter.most_common(limit)
        return {
            "name_labels": [name for name, _ in top_names],
            "name_data": [count for _, count in top_names],
        }

    def get_colors(self, multi_limit=10):
        single_counter = Counter()
        multi_counter = Counter()

        for c in self.cards:
            color = c.color or "Unknown"
            if "/" in color:
                multi_counter[color] += 1
            else:
                single_counter[color] += 1

        top_multi = multi_counter.most_common(multi_limit)
        return {
            "single_color_labels": list(single_counter.keys()),
            "single_color_data": list(single_counter.values()),
            "multicolor_labels": [color for color, _ in top_multi],
            "multicolor_data": [count for _, count in top_multi],
        }

    def get_expansions(self, exclude_prefixes=None):
        exclude_prefixes = exclude_prefixes or []
        counter = Counter()
        expansion_types = {}

        for c in self.cards:
            exp = c.expansion or "Other"

            # Skip card if its expansion matches/starts with an excluded prefix
            if any(exp.upper().startswith(prefix) for prefix in exclude_prefixes):
                continue

            counter[exp] += 1
            if exp not in expansion_types:
                expansion_types[exp] = get_expansion_type(c.card_number)

        sorted_exps = sorted(counter.items(), key=natural_sort_key)
        labels = [e for e, _ in sorted_exps]

        return {
            "expansion_labels": labels,
            "expansion_data": [count for _, count in sorted_exps],
            "expansion_types": [expansion_types.get(e, "Other") for e in labels],
        }

    def get_sec_colors(self):
        counter = Counter()
        for c in self.cards:
            if "SEC" in str(c.rarity).upper():
                color = c.color or "Unknown"
                if "/" in color:
                    for val in color.split("/"):
                        cleaned = val.strip()
                        if cleaned:
                            counter[cleaned] += 1
                else:
                    counter[color] += 1

        return {
            "sec_color_labels": list(counter.keys()),
            "sec_color_data": list(counter.values()),
        }

    def get_subtypes(self, limit=20, exclude_subtypes=None):
        exclude_subtypes = [s.lower() for s in (exclude_subtypes or [])]
        counter = Counter()
        for c in self.cards:
            raw_subtype = c.subtype
            if raw_subtype:
                for val in raw_subtype.split("/"):
                    cleaned = val.strip()
                    if cleaned and cleaned != "-" and cleaned.lower() not in exclude_subtypes:
                        counter[cleaned] += 1

        top_subtypes = counter.most_common(limit)
        return {
            "subtype_labels": [s for s, _ in top_subtypes],
            "subtype_data": [count for _, count in top_subtypes],
        }


@require_GET
def analytics_data(request):
    cards = DigimonCard.objects.all()
    engine = CardAnalyticsEngine(cards)

    data = {
        "total_cards": cards.count(),
    }

    # Check for chart exclusions in headers
    exclude_header = request.headers.get("X-Exclude-Charts", "")
    excluded = [item.strip().lower() for item in exclude_header.split(",")] if exclude_header else []

    # Check for expansion filters
    exclude_exp_param = request.GET.get("exclude_exp", "")
    excluded_expansions = [
        item.strip().upper()
        for item in exclude_exp_param.split(",")
        if item.strip()
    ]

    # Check for subtype filters
    exclude_type_param = request.GET.get("exclude_type", "")
    excluded_types = [
        item.strip()
        for item in exclude_type_param.split(",")
        if item.strip()
    ]

    if "types" not in excluded:
        data.update(engine.get_types())

    if "names" not in excluded:
        data.update(engine.get_names())

    if "colors" not in excluded:
        data.update(engine.get_colors())

    if "expansions" not in excluded:
        data.update(engine.get_expansions(exclude_prefixes=excluded_expansions))

    if "sec_colors" not in excluded:
        data.update(engine.get_sec_colors())

    if "subtypes" not in excluded:
        data.update(engine.get_subtypes(exclude_subtypes=excluded_types))

    return JsonResponse(data)


from django.db.models import Q
from rest_framework import generics
from .serializers import DigimonCardSerializer

def apply_expansion_filter(queryset, expansion: str):
    """
    Shared expansion-matching logic. Matches 'BT19', 'BT18-19', 'BT19-20', etc.
    """
    if not expansion:
        return queryset
    return queryset.filter(
        Q(expansion__iexact=expansion) |
        Q(expansion__icontains=f"{expansion}-") |
        Q(expansion__icontains=f"-{expansion}") |
        Q(card_number__startswith=f"{expansion}-")
    )


class DigimonCardListView(generics.ListAPIView):
    serializer_class = DigimonCardSerializer

    def get_queryset(self):
        queryset = DigimonCard.objects.all()
        expansion = self.request.query_params.get('expansion', None)
        return apply_expansion_filter(queryset, expansion)


def resolve_expansion_name(expansion_code: str, expansion_map: dict) -> str:
    """
    Resolve a card's expansion code to a display name using a preloaded
    {expansion_code: expansion_name} map. Mirrors the exact-match then
    range-containment logic used in DigimonCardSerializer.get_expansion_name.
    """
    if not expansion_code:
        return "Unknown Expansion"

    # 1. Direct match on exact code (e.g. "BT18-19")
    name = expansion_map.get(expansion_code)
    if name:
        return name

    # 2. Range containment: expansion_code ("BT19") found inside a combined
    #    code key ("BT18-19" / "BT19-20")
    for code, name in expansion_map.items():
        if expansion_code in code and name:
            return name

    return expansion_code


@require_GET
def cards_by_name(request):
    """
    Return all cards with a given English name.
    Optional `expansion` query param filters to a specific set/range.
    """
    name = request.GET.get("name", "").strip()
    expansion = request.GET.get("expansion", "").strip()

    if not name:
        return JsonResponse(
            {"error": "Missing name parameter."},
            status=400,
        )

    cards = DigimonCard.objects.filter(name__iexact=name).prefetch_related('images')
    cards = apply_expansion_filter(cards, expansion)
    cards = cards.order_by("card_number")

    expansion_map = dict(
        CardExpansion.objects.values_list("expansion_code", "expansion_name")
    )

    data = {
        "name": name,
        "expansion": expansion or None,
        "count": cards.count(),
        "cards": [
            {
                **card.data,
                "expansion": card.expansion,
                "expansion_name": resolve_expansion_name(card.expansion, expansion_map),

                "images": [
                    {
                        "image_url": img.image_url,
                        "variant_type": img.variant_type,
                        "is_primary": img.is_primary,
                    }
                    for img in card.images.all()
                ]
            }
            for card in cards
        ],
    }
    
    return JsonResponse(data)


@require_GET
def statistics_schema(request):
    return JsonResponse({
        "fields": get_analytics_fields(),
        "categorical_fields": list(get_categorical_fields().keys()),
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

    include_baseline = request.GET.get("baseline", "1") != "0"

    result = conditional_distribution(
        DigimonCard,
        given_field,
        target_field,
        given_value,
        include_baseline=include_baseline,
    )

    return JsonResponse(result)


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

    diagnostics = cramers_v_with_diagnostics(
        rows,
        first_field,
        second_field,
    )

    return JsonResponse({
        "fields": {
            "first": first_field,
            "second": second_field,
        },
        "cramers_v": diagnostics["cramers_v"],
        "sample_size": diagnostics["sample_size"],
        "reliable": diagnostics["reliable"],
        "low_expected_cell_ratio": diagnostics["low_expected_cell_ratio"],
    })


@require_GET
def cards_by_type(request):
    """
    Return paginated cards matching a specific subtype.
    Example: /api/cards-by-type/?type=Vaccine&page=1
    """
    card_type = request.GET.get("type", "").strip()

    if not card_type:
        return JsonResponse({"error": "Missing type parameter."}, status=400)

    try:
        page_number = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page_number = 1

    cards = DigimonCard.objects.filter(subtype__icontains=card_type).order_by("card_number")

    paginator = Paginator(cards, 25)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    data = {
        "type": card_type,
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
        "cards": [card.data for card in page_obj.object_list],
    }

    return JsonResponse(data)