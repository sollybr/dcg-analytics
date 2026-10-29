"""Authentication for the cron-triggered sync endpoint."""
import hmac

from django.conf import settings

from .api import json_error

_BEARER = "Bearer "


def _supplied_token(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith(_BEARER):
        bearer = auth_header[len(_BEARER):].strip()
        if bearer:
            return bearer
    return (
        request.headers.get("X-Card-Sync-Token")
        or request.GET.get("token")
        or ""
    )


def check_cron_token(request):
    """Return an error response if the request isn't authorised, else None."""
    expected = getattr(settings, "CRON_SECRET", None)
    if not expected:
        return json_error("Server cron secret is not configured.", status=500)

    supplied = _supplied_token(request)
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        return json_error("Unauthorized request.", status=403)
    return None
