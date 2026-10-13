"""Настройка pytest: подключение настроек Django для тестов веб-слоя."""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workout_app.settings")
django.setup()
