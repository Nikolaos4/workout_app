"""Админ-зона: результаты пользователей за период."""

from django.contrib import admin

from .models import Result


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("user", "period_start", "period_end")
    filter_horizontal = ("workouts",)
