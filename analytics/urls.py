from django.urls import path
from .views import analytics_data, cards_by_name, sync_cards_view, cards_by_type

urlpatterns = [
    path("api/analytics/", analytics_data),
    path("api/cards/", cards_by_name),
    path("api/sync-cards/", sync_cards_view),
    path("api/cards-by-type/", cards_by_type),
]