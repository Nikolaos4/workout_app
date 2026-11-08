"""Админ-зона: управление пользователями сервиса."""

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "registered_at")
    search_fields = ("name",)
