"""Админ-зона: справочник упражнений."""

from django.contrib import admin

from .models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group")
    list_filter = ("muscle_group",)
    search_fields = ("name", "muscle_group")
