"""Маршруты приложения workouts."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.workouts, name="workouts"),
    path("<int:workout_id>/", views.workout_detail, name="workout_detail"),
]
