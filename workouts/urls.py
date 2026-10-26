"""Маршруты приложения workouts."""

from django.urls import path

from . import views

app_name = "workouts"

urlpatterns = [
    path("", views.workouts, name="list"),
    path("<int:workout_id>/", views.workout_detail, name="detail"),
]
