"""Маршруты приложения exercises."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.exercises, name="exercises"),
    path("<int:exercise_id>/", views.exercise_detail, name="exercise_detail"),
]
