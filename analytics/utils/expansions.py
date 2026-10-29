"""Expansion-code helpers: type prefix, queryset filtering, name lookup."""
import re

from django.db.models import Q

from ..models import CardExpansion

_PREFIX = re.compile(r"^([A-Z]+)")


def get_expansion_type(card_number):
    if not card_number:
        return "Other"
    match = _PREFIX.match(card_number)
    return match.group(1) if match else "Other"


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


def get_expansion_map() -> dict:
    """{expansion_code: expansion_name} for every known expansion."""
    return dict(
        CardExpansion.objects.values_list("expansion_code", "expansion_name")
    )


def resolve_expansion_name(expansion_code: str, expansion_map: dict) -> str:
    """
    Resolve a card's expansion code to a display name using a preloaded
    {expansion_code: expansion_name} map. Exact match first, then
    range-containment ("BT19" inside "BT18-19").
    """
    if not expansion_code:
        return "Unknown Expansion"

    name = expansion_map.get(expansion_code)
    if name:
        return name

    for code, name in expansion_map.items():
        if expansion_code in code and name:
            return name

    return expansion_code
