"""Модель пользователя предметной области «Сервис учета тренировок».

Это не встроенная модель аутентификации Django (django.contrib.auth.User):
она хранит только данные пользователя сервиса и не отвечает за вход в систему.
"""

from django.db import models
from django.utils import timezone


class User(models.Model):
    """Пользователь сервиса: имя и дата регистрации."""

    name = models.CharField(
        max_length=200,
        verbose_name="Имя пользователя",
    )
    registered_at = models.DateField(
        default=timezone.localdate,
        verbose_name="Дата регистрации",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
