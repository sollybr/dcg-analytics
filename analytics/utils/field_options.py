"""Autocomplete values for /api/field-options/."""
from collections import Counter

from django.db.models import Count

from ..models import DigimonCard
from .text import split_multi

# Fields /api/field-options/ can list values for. The bool says whether the
# stored string is a "/"-separated list ("Red/Blue") that should be split
# into individual values. Keep the keys in sync with DEFAULT_FIELD_OPTIONS
# in the frontend's fieldOptions.ts.
FIELD_OPTION_FIELDS = {
    "name": False,
    "color": True,
    "rarity": False,
    "expansion": False,
    "subtype": True,
    "card_type": False,
}

FIELD_OPTIONS_DEFAULT_LIMIT = 20
FIELD_OPTIONS_MAX_LIMIT = 100


def get_field_options(field, query="", limit=FIELD_OPTIONS_DEFAULT_LIMIT):
    """
    Distinct values (with card counts) for one card field. `field` must be a
    key of FIELD_OPTION_FIELDS.

    Matching is a case-insensitive substring on each individual value;
    results that start with `query` come first, then by count.
    """
    cards = DigimonCard.objects.exclude(**{field: ""})

    # Narrowing in SQL is safe for split fields too: any part containing
    # `query` means the whole stored string contains it.
    if query:
        cards = cards.filter(**{f"{field}__icontains": query})

    # order_by() clears Meta.ordering (card_number), which would otherwise
    # be added to GROUP BY and stop the counts from aggregating.
    grouped = (
        cards.order_by()
        .values_list(field)
        .annotate(count=Count("id"))
    )

    splits = FIELD_OPTION_FIELDS[field]
    needle = query.lower()
    counts = Counter()

    for raw, count in grouped:
        parts = split_multi(raw) if splits else [raw.strip()]

        for value in parts:
            if not value or value == "-":
                continue
            if needle and needle not in value.lower():
                continue
            counts[value] += count

    ordered = sorted(
        counts.items(),
        key=lambda item: (
            not item[0].lower().startswith(needle),
            -item[1],
            item[0].lower(),
        ),
    )

    return [{"value": value, "count": count} for value, count in ordered[:limit]]
