
from django.urls import path

from .views import (
    analytics_data,
    cards_by_name,
    sync_cards_view,
    cards_by_type,
    statistics_schema,
    statistics_distribution,
    statistics_association,
)


urlpatterns = [
    path("analytics/", analytics_data),
    path("cards/", cards_by_name),
    path("sync-cards/", sync_cards_view),
    path("cards-by-type/", cards_by_type),
    path(
        "statistics/schema/",
        statistics_schema,
        name="statistics-schema",
    ),
    path(
        "statistics/distribution/",
        statistics_distribution,
        name="statistics-distribution",
    ),
    path(
        "statistics/association/",
        statistics_association,
        name="statistics-association",
    ),
]
