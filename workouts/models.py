"""Модели тренировки и выполненных в ней упражнений.

Связи:
    * User 1 — N Workout (у пользователя много тренировок);
    * Workout N — M Exercise через WorkoutExercise (в тренировке много
      упражнений, одно упражнение встречается во многих тренировках;
      подходы, повторения и вес хранятся в связующей модели).
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


from .querysets import WorkoutQuerySet


class Workout(models.Model):
    """Тренировка пользователя на определённую дату."""

    objects = WorkoutQuerySet.as_manager()

    class WorkoutType(models.TextChoices):
        CARDIO = "кардио", "Кардио"
        STRENGTH = "силовая", "Силовая"

    # PROTECT: нельзя удалить пользователя, у которого есть тренировки.
    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="workouts",
        verbose_name="Пользователь",
    )
    workout_date = models.DateField(verbose_name="Дата тренировки")
    workout_type = models.CharField(
        max_length=20,
        choices=WorkoutType.choices,
        verbose_name="Тип тренировки",
    )
    duration_min = models.PositiveIntegerField(
        default=60,
        verbose_name="Длительность, мин",
    )

    class Status(models.TextChoices):
        ACTIVE = "active", "активна"
        CANCELLED = "cancelled", "Отменена"
        COMPLETED = "completed", "Завершена"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )

    @property
    def is_cancelled(self):
        """Совместимость шаблонов ПР9; значение определяется статусом."""
        return self.status == self.Status.CANCELLED

    exercises = models.ManyToManyField(
        "exercises.Exercise",
        through="WorkoutExercise",
        related_name="workouts",
        verbose_name="Упражнения",
    )

    def clean(self):
        """Правило предметной области: дата тренировки не в будущем."""
        if self.workout_date and self.workout_date > timezone.localdate():
            raise ValidationError(
                {"workout_date": "Дата тренировки не может быть в будущем."}
            )

    def cancel(self):
        """Отменить тренировку и сохранить только изменённое поле."""
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])

    def __str__(self):
        return f"{self.workout_date:%d.%m.%Y} — {self.workout_type} ({self.user})"

    class Meta:
        ordering = ["-workout_date", "-pk"]
        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"


class WorkoutExercise(models.Model):
    """Выполненное упражнение: строка тренировки с подходами и весом."""

    # CASCADE: строки принадлежат тренировке и удаляются вместе с ней.
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name="workout_exercises",
        verbose_name="Тренировка",
    )
    # PROTECT: упражнение из справочника нельзя удалить, пока оно используется.
    exercise = models.ForeignKey(
        "exercises.Exercise",
        on_delete=models.PROTECT,
        related_name="workout_exercises",
        verbose_name="Упражнение",
    )
    sets = models.PositiveIntegerField(verbose_name="Подходы")
    reps = models.PositiveIntegerField(verbose_name="Повторения")
    weight = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Рабочий вес, кг",
    )

    @property
    def tonnage(self):
        """Тоннаж строки: подходы × повторения × вес."""
        return self.sets * self.reps * self.weight

    def __str__(self):
        return f"{self.exercise}: {self.sets}×{self.reps}, {self.weight:g} кг"

    class Meta:
        ordering = ["pk"]
        verbose_name = "Выполненное упражнение"
        verbose_name_plural = "Выполненные упражнения"
        constraints = [
            models.CheckConstraint(
                condition=Q(weight__gte=0),
                name="workoutexercise_weight_gte_0",
            ),
        ]
