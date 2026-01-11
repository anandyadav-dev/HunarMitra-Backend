"""
URL configuration for core app.
"""

from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("health/", views.health_check, name="health"),
    path("theme/", views.theme, name="theme"),
    path("app-config/", views.AppConfigView.as_view(), name="app-config"),
    path("config/theme/", views.ThemeConfigView.as_view(), name="theme-config"),
    path("config/i18n/", views.I18nView.as_view(), name="i18n"),
]
