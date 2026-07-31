from django.urls import path
from .views import api_dashboard

urlpatterns = [
    path('api/dashboard/', api_dashboard, name='api_dashboard'),
]