"""Pure string helpers (no Django imports)."""
import re

_DIGITS = re.compile(r"(\d+)")


def natural_sort_key(text):
    """Sort key that orders embedded numbers numerically (BT1, BT2, BT10)."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in _DIGITS.split(text)
    ]


def split_multi(raw, sep="/"):
    """Split a 'Red/Blue' style value into stripped, non-empty parts."""
    if not raw:
        return []
    return [part.strip() for part in raw.split(sep) if part.strip()]
