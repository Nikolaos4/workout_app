"""Маршруты приложения exercises."""

from django.urls import path

from . import views

app_name = "exercises"

urlpatterns = [
    path("", views.exercises, name="list"),
    path("search/", views.exercise_search, name="search"),
    path("<int:exercise_id>/", views.exercise_detail, name="detail"),
]
