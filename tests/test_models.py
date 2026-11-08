"""Тесты моделей Django (ПР9): поля, связи, ограничения и операции ORM."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from exercises.models import Exercise
from results.models import Result
from users.models import User
from workouts.models import Workout, WorkoutExercise
from workouts.services import create_workout

pytestmark = pytest.mark.django_db


def test_str_methods(base_data):
    assert str(base_data.user) == "Николай Аниканов"
    assert str(base_data.bench) == "Жим лёжа"
    assert "07.09.2026" in str(base_data.workout)
    assert str(WorkoutExercise.objects.first()) == "Жим лёжа: 3×8, 80 кг"


def test_primary_key_is_created_automatically(base_data):
    assert base_data.user.pk == base_data.user.id == 1


def test_foreign_key_forward_access(base_data):
    workout = Workout.objects.get(pk=1)
    assert workout.user == base_data.user
    assert workout.user_id == 1


def test_reverse_access_through_related_name(base_data):
    assert list(base_data.user.workouts.all()) == [base_data.workout]
    assert base_data.workout.workout_exercises.count() == 3
    assert base_data.bench.workout_exercises.count() == 1


def test_many_to_many_through_workout_exercise(base_data):
    assert set(base_data.workout.exercises.all()) == {
        base_data.bench,
        base_data.squat,
        base_data.curl,
    }
    assert list(base_data.bench.workouts.all()) == [base_data.workout]


def test_tonnage_property(base_data):
    first = base_data.workout.workout_exercises.first()
    assert first.tonnage == 3 * 8 * 80


def test_cancel_updates_only_flag(base_data):
    workout = base_data.workout
    workout.cancel()
    workout.refresh_from_db()
    assert workout.is_cancelled is True


def test_default_values(base_data):
    workout = Workout.objects.create(
        user=base_data.user, workout_date=date(2026, 9, 1), workout_type="кардио"
    )
    assert workout.duration_min == 0
    assert workout.is_cancelled is False


def test_future_date_is_rejected_by_validation(base_data):
    workout = Workout(
        user=base_data.user,
        workout_date=timezone.localdate() + timedelta(days=1),
        workout_type="силовая",
    )
    with pytest.raises(ValidationError) as error:
        workout.full_clean()
    assert "workout_date" in error.value.message_dict


def test_unknown_workout_type_is_rejected_by_validation(base_data):
    workout = Workout(
        user=base_data.user, workout_date=date(2026, 9, 1), workout_type="йога"
    )
    with pytest.raises(ValidationError) as error:
        workout.full_clean()
    assert "workout_type" in error.value.message_dict


def test_negative_sets_are_rejected_by_database(base_data):
    with pytest.raises(IntegrityError), transaction.atomic():
        WorkoutExercise.objects.create(
            workout=base_data.workout, exercise=base_data.bench, sets=-1, reps=1
        )


def test_negative_weight_is_rejected_by_database(base_data):
    with pytest.raises(IntegrityError), transaction.atomic():
        WorkoutExercise.objects.create(
            workout=base_data.workout,
            exercise=base_data.bench,
            sets=1,
            reps=1,
            weight=-5,
        )


def test_result_period_must_not_end_before_start(base_data):
    with pytest.raises(IntegrityError), transaction.atomic():
        Result.objects.create(
            user=base_data.user,
            period_start=date(2026, 9, 30),
            period_end=date(2026, 9, 1),
        )


def test_result_contains_workouts(base_data):
    result = Result.objects.create(
        user=base_data.user,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
    )
    result.workouts.add(base_data.workout)
    assert list(base_data.workout.results.all()) == [result]
    assert list(base_data.user.results.all()) == [result]


# --- on_delete: PROTECT и CASCADE -----------------------------------------


def test_user_with_workouts_cannot_be_deleted(base_data):
    with pytest.raises(ProtectedError):
        base_data.user.delete()


def test_used_exercise_cannot_be_deleted(base_data):
    with pytest.raises(ProtectedError):
        base_data.bench.delete()


def test_deleting_workout_removes_its_rows(base_data):
    base_data.workout.delete()
    assert WorkoutExercise.objects.count() == 0
    assert Exercise.objects.count() == 3
    assert User.objects.count() == 1


# --- CRUD -------------------------------------------------------------------


def test_crud_cycle():
    user = User.objects.create(name="Тест")
    assert User.objects.filter(name="Тест").exists()

    user.name = "Тест 2"
    user.save()
    assert User.objects.get(pk=user.pk).name == "Тест 2"

    user.delete()
    assert not User.objects.filter(pk=user.pk).exists()


def test_registered_at_defaults_to_today():
    user = User.objects.create(name="Новый")
    assert user.registered_at == timezone.localdate()


# --- создание тренировки по правилам предметной области ----------------------


def test_create_workout_with_exercises(base_data):
    workout = create_workout(
        base_data.user,
        date(2026, 9, 8),
        "силовая",
        40,
        [{"exercise": base_data.bench, "sets": 3, "reps": 5, "weight": 60}],
    )
    assert workout.workout_exercises.count() == 1
    assert Workout.objects.count() == 2


def test_create_workout_without_exercises_is_rejected(base_data):
    with pytest.raises(ValidationError):
        create_workout(base_data.user, date(2026, 9, 8), "силовая", 40, [])
    assert Workout.objects.count() == 1


def test_create_workout_with_future_date_is_rejected(base_data):
    future = timezone.localdate() + timedelta(days=3)
    items = [{"exercise": base_data.bench, "sets": 1, "reps": 1, "weight": 1}]
    with pytest.raises(ValidationError):
        create_workout(base_data.user, future, "силовая", 40, items)
    assert Workout.objects.count() == 1


def test_create_workout_rolls_back_on_invalid_row(base_data):
    items = [
        {"exercise": base_data.bench, "sets": 1, "reps": 1, "weight": 1},
        {"exercise": base_data.squat, "sets": 1, "reps": 1, "weight": -1},
    ]
    with pytest.raises(ValidationError):
        create_workout(base_data.user, date(2026, 9, 8), "силовая", 40, items)
    assert Workout.objects.count() == 1
    assert WorkoutExercise.objects.count() == 3


def test_migrations_are_up_to_date():
    from django.core.management import call_command

    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
