import logging

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from rest_framework import generics

from .models import DigimonCard
from .serializers import DigimonCardSerializer
from .statistics.schema import (
    get_analytics_fields,
    get_categorical_fields,
)
from .utils.analytics import CardAnalyticsEngine
from .utils.api import json_error, parse_csv, parse_int
from .utils.auth import check_cron_token
from .utils.cards import serialize_cards
from .utils.expansions import apply_expansion_filter
from .utils.field_options import (
    FIELD_OPTION_FIELDS,
    FIELD_OPTIONS_DEFAULT_LIMIT,
    FIELD_OPTIONS_MAX_LIMIT,
    get_field_options,
)

logger = logging.getLogger(__name__)

CARDS_BY_TYPE_PAGE_SIZE = 15


@require_http_methods(["POST", "GET"])
def sync_cards_view(request):
    denied = check_cron_token(request)
    if denied is not None:
        return denied

    # Imported here so the sync dependencies only load when this endpoint runs.
    from .card_sync import sync_cards

    try:
        return JsonResponse(sync_cards(), status=200)
    except Exception:
        logger.exception("Card sync failed.")
        return json_error("An internal error has occurred.", status=500)


@require_GET
def analytics_data(request):
    cards = DigimonCard.objects.all()
    engine = CardAnalyticsEngine(cards)

    return JsonResponse({
        "total_cards": cards.count(),
        **engine.compute(
            excluded=parse_csv(request.headers.get("X-Exclude-Charts"), str.lower),
            exclude_expansions=parse_csv(request.GET.get("exclude_exp"), str.upper),
            exclude_subtypes=parse_csv(request.GET.get("exclude_type")),
        ),
    })


class DigimonCardListView(generics.ListAPIView):
    serializer_class = DigimonCardSerializer

    def get_queryset(self):
        queryset = DigimonCard.objects.all()
        expansion = self.request.query_params.get("expansion", None)
        return apply_expansion_filter(queryset, expansion)


@require_GET
def cards_by_name(request):
    """
    Return all cards with a given English name.
    Optional `expansion` query param filters to a specific set/range.
    """
    name = request.GET.get("name", "").strip()
    expansion = request.GET.get("expansion", "").strip()

    if not name:
        return json_error("Missing name parameter.")

    cards = DigimonCard.objects.filter(name__iexact=name).prefetch_related("images")
    cards = apply_expansion_filter(cards, expansion).order_by("card_number")
    serialized = serialize_cards(cards)

    return JsonResponse({
        "name": name,
        "expansion": expansion or None,
        "count": len(serialized),
        "cards": serialized,
    })


@require_GET
def cards_by_type(request):
    """
    Return paginated cards matching a specific subtype.
    Example: /api/cards-by-type/?type=Vaccine&page=1
    """
    card_type = request.GET.get("type", "").strip()

    if not card_type:
        return json_error("Missing type parameter.")

    cards = (
        DigimonCard.objects.filter(subtype__icontains=card_type)
        .order_by("card_number")
        .prefetch_related("images")
    )

    paginator = Paginator(cards, CARDS_BY_TYPE_PAGE_SIZE)
    # get_page(): bad page -> first page, out-of-range page -> last page.
    page_obj = paginator.get_page(request.GET.get("page"))

    return JsonResponse({
        "type": card_type,
        "total_count": paginator.count,
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
        "cards": serialize_cards(page_obj.object_list),
    })


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

    for label, field in (("given field", given_field), ("target field", target_field)):
        if field not in categorical_fields:
            return json_error(f"Invalid {label}: {field}")

    if not given_value:
        return json_error("Missing 'value' parameter.")

    # Imported here so the stats dependencies only load for this endpoint.
    from .statistics.distributions import conditional_distribution

    return JsonResponse(
        conditional_distribution(
            DigimonCard,
            given_field,
            target_field,
            given_value,
            include_baseline=request.GET.get("baseline", "1") != "0",
        )
    )


@require_GET
def statistics_association(request):
    first_field = request.GET.get("first")
    second_field = request.GET.get("second")

    categorical_fields = get_categorical_fields()

    for field in (first_field, second_field):
        if field not in categorical_fields:
            return json_error(f"Invalid field: {field}")

    # Imported here so the stats dependencies only load for this endpoint.
    from .statistics.associations import cramers_v_with_diagnostics

    rows = list(DigimonCard.objects.values(first_field, second_field))
    diagnostics = cramers_v_with_diagnostics(rows, first_field, second_field)

    return JsonResponse({
        "fields": {"first": first_field, "second": second_field},
        "cramers_v": diagnostics["cramers_v"],
        "sample_size": diagnostics["sample_size"],
        "reliable": diagnostics["reliable"],
        "low_expected_cell_ratio": diagnostics["low_expected_cell_ratio"],
    })


@require_GET
def field_options(request):
    """
    Distinct values (with card counts) for one card field, for autocomplete.
    Example: /api/field-options/?field=subtype&q=vac&limit=20
    """
    field = request.GET.get("field", "")

    if field not in FIELD_OPTION_FIELDS:
        return json_error(f"Invalid field: {field}")

    query = request.GET.get("q", "").strip()
    limit = parse_int(
        request.GET.get("limit"),
        FIELD_OPTIONS_DEFAULT_LIMIT,
        minimum=1,
        maximum=FIELD_OPTIONS_MAX_LIMIT,
    )

    return JsonResponse({
        "field": field,
        "options": get_field_options(field, query, limit),
    })
