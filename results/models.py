"""Модель результата пользователя за период времени."""

from django.db import models
from django.db.models import F, Q


class Result(models.Model):
    """Результат за период: пользователь, даты периода и тренировки в нём."""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="results",
        verbose_name="Пользователь",
    )
    period_start = models.DateField(verbose_name="Начало периода")
    period_end = models.DateField(verbose_name="Конец периода")
    # Связь «многие ко многим»: одна тренировка может войти в разные периоды.
    workouts = models.ManyToManyField(
        "workouts.Workout",
        related_name="results",
        blank=True,
        verbose_name="Тренировки периода",
    )

    def __str__(self):
        return f"{self.user}: {self.period_start:%d.%m.%Y} – {self.period_end:%d.%m.%Y}"

    class Meta:
        ordering = ["-period_end", "-pk"]
        verbose_name = "Результат за период"
        verbose_name_plural = "Результаты за период"
        constraints = [
            models.CheckConstraint(
                condition=Q(period_end__gte=F("period_start")),
                name="result_period_end_gte_start",
            ),
        ]
