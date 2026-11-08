"""Модель справочника упражнений."""

from django.db import models


class Exercise(models.Model):
    """Упражнение: название и рабочая группа мышц."""

    name = models.CharField(
        max_length=200,
        verbose_name="Название упражнения",
    )
    muscle_group = models.CharField(
        max_length=100,
        verbose_name="Группа мышц",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"
