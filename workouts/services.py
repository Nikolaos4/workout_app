"""Операции создания тренировок с соблюдением правил предметной области."""

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Workout, WorkoutExercise


@transaction.atomic
def create_workout(user, workout_date, workout_type, duration_min, items):
    """Создать тренировку со строками упражнений.

    items — список словарей с ключами exercise, sets, reps, weight (weight
    можно не указывать). Правила: в тренировке есть хотя бы одно упражнение,
    дата не в будущем, подходы, повторения и вес не отрицательны. При
    нарушении правил выбрасывается ValidationError, и ничего не сохраняется.
    """
    if not items:
        raise ValidationError("Тренировка должна содержать хотя бы одно упражнение.")

    workout = Workout(
        user=user,
        workout_date=workout_date,
        workout_type=workout_type,
        duration_min=duration_min,
    )
    workout.full_clean()
    workout.save()

    for item in items:
        row = WorkoutExercise(workout=workout, **item)
        row.full_clean()
        row.save()
    return workout
