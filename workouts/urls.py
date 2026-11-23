"""Маршруты приложения workouts."""

from django.urls import path

from . import views

app_name = "workouts"

urlpatterns = [
    path("", views.workouts, name="list"),
    path("create/", views.workout_create, name="create"),
    path("<int:workout_id>/edit/", views.workout_edit, name="edit"),
    path("<int:workout_id>/cancel/", views.workout_cancel, name="cancel"),
    path("statistics/", views.statistics, name="statistics"),
    path("<int:workout_id>/", views.workout_detail, name="detail"),
]
