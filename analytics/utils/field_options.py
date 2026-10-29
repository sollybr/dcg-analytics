"""Autocomplete values for /api/field-options/."""
from collections import Counter, defaultdict

from django.db.models import Count, Q

from ..models import CardExpansion, DigimonCard
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

# Field whose values are expansion codes; its options are also searchable
# and labelled by expansion name.
EXPANSION_FIELD = "expansion"

EXPANSION_LABEL_OVERRIDES = {"P": "Promos"}

def get_expansion_names():
    """
    Upper-cased code -> [names]. A code can map to several names when
    regional releases merge expansions.
    """
    names = defaultdict(list)
    rows = (
        CardExpansion.objects
        .exclude(expansion_name="")
        .order_by("expansion_name")
        .values_list("expansion_code", "expansion_name")
    )
    for code, name in rows:
        key = code.strip().upper()
        if name not in names[key]:
            names[key].append(name)
    return names


def _search_names(code, names_by_code):
    """Every name a query may match for this code (overrides included)."""
    names = list(names_by_code.get(code, ()))
    override = EXPANSION_LABEL_OVERRIDES.get(code)
    if override:
        names.append(override)
    return names


def get_field_options(field, query="", limit=FIELD_OPTIONS_DEFAULT_LIMIT):
    """
    Distinct values (with card counts) for one card field. `field` must be a
    key of FIELD_OPTION_FIELDS.

    Matching is a case-insensitive substring on each individual value;
    results that start with `query` come first, then by count.

    For the expansion field, the query also matches expansion names, and each
    option carries a `label` with the name(s) for display. `value` stays the
    code, which is what the card filter uses. Codes in
    EXPANSION_LABEL_OVERRIDES display their fixed label instead of the list
    of names. For every other field, `label` equals `value`.
    """
    needle = query.lower()
    is_expansion = field == EXPANSION_FIELD
    names_by_code = get_expansion_names() if is_expansion else {}

    # Upper-cased codes whose expansion name (or override label) contains
    # the query.
    name_matched = set()
    if needle and is_expansion:
        codes = set(names_by_code) | set(EXPANSION_LABEL_OVERRIDES)
        name_matched = {
            code
            for code in codes
            if any(
                needle in name.lower()
                for name in _search_names(code, names_by_code)
            )
        }

    cards = DigimonCard.objects.exclude(**{field: ""})

    # Narrowing in SQL is safe for split fields too: any part containing
    # `query` means the whole stored string contains it.
    if query:
        condition = Q(**{f"{field}__icontains": query})
        if name_matched:
            # Cover the stored code being upper or lower case.
            variants = name_matched | {code.lower() for code in name_matched}
            condition |= Q(**{f"{field}__in": list(variants)})
        cards = cards.filter(condition)

    # order_by() clears Meta.ordering (card_number), which would otherwise
    # be added to GROUP BY and stop the counts from aggregating.
    grouped = (
        cards.order_by()
        .values_list(field)
        .annotate(count=Count("id"))
    )

    splits = FIELD_OPTION_FIELDS[field]
    counts = Counter()

    for raw, count in grouped:
        parts = split_multi(raw) if splits else [raw.strip()]

        for value in parts:
            if not value or value == "-":
                continue
            if (
                needle
                and needle not in value.lower()
                and value.upper() not in name_matched
            ):
                continue
            counts[value] += count

    def starts_with_query(value):
        if value.lower().startswith(needle):
            return True
        if not is_expansion:
            return False
        return any(
            name.lower().startswith(needle)
            for name in _search_names(value.upper(), names_by_code)
        )

    ordered = sorted(
        counts.items(),
        key=lambda item: (
            not starts_with_query(item[0]),
            -item[1],
            item[0].lower(),
        ),
    )

    def label_for(value):
        if not is_expansion:
            return value
        override = EXPANSION_LABEL_OVERRIDES.get(value.upper())
        if override:
            return override
        names = names_by_code.get(value.upper())
        return " / ".join(names) if names else value

    return [
        {"value": value, "label": label_for(value), "count": count}
        for value, count in ordered[:limit]
    ]
