from django.urls import path

from .views import analytics_data, cards_by_name


urlpatterns = [
    path(
        'analytics/',
        analytics_data,
        name='analytics',
    ),
    path(
        'cards/',
        cards_by_name,
        name='cards_by_name',
    ),
]