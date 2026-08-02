from django.urls import path
from .views import analytics_data, cards_by_name, sync_cards_view

urlpatterns = [
    path("api/analytics/", analytics_data, name="analytics_data"),
    path("api/cards/", cards_by_name, name="cards_by_name"),
    path("api/sync-cards/", sync_cards_view, name="sync_cards"),
]