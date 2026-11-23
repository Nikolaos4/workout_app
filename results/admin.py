"""Админ-зона: результаты пользователей за период."""

from django.contrib import admin

from .models import Result


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("user", "period_start", "period_end")
    filter_horizontal = ("workouts",)

    list_select_related = ("user",)
    search_fields = ("user__name",)
    list_filter = ("period_start", "period_end")
    ordering = ("-period_end", "-pk")
    readonly_fields = ("id",)
    list_per_page = 20
