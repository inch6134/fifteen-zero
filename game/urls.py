from django.urls import path
from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("api/health/", views.HealthView.as_view(), name="health"),
    path("api/spin/", views.SpinView.as_view(), name="spin"),
    path("api/players/<int:club_era_id>/", views.PlayerListView.as_view(), name="spin"),
    path("api/sessions/", views.SessionView.as_view(), name="sessions"),
]
