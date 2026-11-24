"""Маршруты приложения exercises."""

from django.urls import path

from . import views

app_name = "exercises"

urlpatterns = [
    path("", views.exercises, name="list"),
    path("create/", views.exercise_create, name="create"),
    path("<int:exercise_id>/edit/", views.exercise_edit, name="edit"),
    path("search/", views.exercise_search, name="search"),
    path("by-slug/<slug:slug>/", views.exercise_detail, name="detail_slug"),
    path("<int:exercise_id>/", views.exercise_detail, name="detail"),
]
