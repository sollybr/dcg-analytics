"""Small request/response helpers shared by the API views."""
from django.http import JsonResponse


def json_error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def parse_int(value, default, minimum=None, maximum=None):
    """int(value), falling back to `default` and clamped to [minimum, maximum]."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def parse_csv(value, transform=None):
    """'a, b,,c' -> ['a', 'b', 'c'], optionally mapping `transform` over items."""
    items = [item.strip() for item in (value or "").split(",")]
    items = [item for item in items if item]
    return [transform(item) for item in items] if transform else items
