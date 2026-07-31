from django.contrib import admin
from django.urls import path
from analytics.views import analytics_data

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/analytics/', analytics_data),
]