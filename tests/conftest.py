"""Общие фикстуры тестов, работающих с базой Django через ORM.

Тестовая база создаётся pytest-django отдельно (в памяти), поэтому рабочие
файлы db.sqlite3 и data/workout_app.sqlite тестами не затрагиваются.
"""

from datetime import date
from types import SimpleNamespace

import pytest

from exercises.models import Exercise
from users.models import User
from workouts.models import Workout, WorkoutExercise


@pytest.fixture
def base_data(db):
    """Данные, равные содержимому data/*.json: 1 пользователь, 3 упражнения,
    1 тренировка с тремя строками (тоннаж 1920 + 2000 + 960 кг)."""
    user = User.objects.create(
        pk=1, name="Николай Аниканов", registered_at=date(2026, 9, 7)
    )
    bench = Exercise.objects.create(pk=1, name="Жим лёжа", muscle_group="Грудь")
    squat = Exercise.objects.create(pk=2, name="Присед", muscle_group="Ноги")
    curl = Exercise.objects.create(pk=3, name="Молотки", muscle_group="Бицепс")
    workout = Workout.objects.create(
        pk=1,
        user=user,
        workout_date=date(2026, 9, 7),
        workout_type="силовая",
        duration_min=60,
    )
    WorkoutExercise.objects.bulk_create(
        [
            WorkoutExercise(workout=workout, exercise=bench, sets=3, reps=8, weight=80),
            WorkoutExercise(
                workout=workout, exercise=squat, sets=2, reps=10, weight=100
            ),
            WorkoutExercise(workout=workout, exercise=curl, sets=4, reps=12, weight=20),
        ]
    )
    return SimpleNamespace(
        user=user, bench=bench, squat=squat, curl=curl, workout=workout
    )


@pytest.fixture
def demo_data(base_data):
    """base_data плюс демонстрационные записи (как в sql/demo_data.sql):
    всего 2 пользователя и 5 тренировок, одна из них отменена."""
    maria = User.objects.create(
        pk=2, name="Мария Петрова", registered_at=date(2026, 9, 10)
    )
    rows = [
        (2, base_data.user, date(2026, 9, 14), "силовая", 55, False),
        (3, base_data.user, date(2026, 9, 21), "кардио", 30, False),
        (4, maria, date(2026, 9, 15), "силовая", 45, False),
        (5, maria, date(2026, 9, 22), "силовая", 50, True),
    ]
    for pk, user, day, kind, minutes, cancelled in rows:
        Workout.objects.create(
            pk=pk,
            user=user,
            workout_date=day,
            workout_type=kind,
            duration_min=minutes,
            status="cancelled" if cancelled else "active",
        )
    bench, squat, curl = base_data.bench, base_data.squat, base_data.curl
    WorkoutExercise.objects.bulk_create(
        [
            WorkoutExercise(workout_id=2, exercise=bench, sets=4, reps=8, weight=85),
            WorkoutExercise(workout_id=2, exercise=curl, sets=3, reps=12, weight=22.5),
            WorkoutExercise(workout_id=3, exercise=squat, sets=1, reps=10, weight=0),
            WorkoutExercise(workout_id=4, exercise=bench, sets=3, reps=10, weight=40),
            WorkoutExercise(workout_id=4, exercise=squat, sets=3, reps=8, weight=60),
            WorkoutExercise(workout_id=5, exercise=bench, sets=3, reps=10, weight=45),
        ]
    )
    base_data.maria = maria
    return base_data
