"""Тесты функций работы с тренировками."""

from datetime import date, timedelta

import pytest

from workouts import (
    cancel_workout,
    create_workout,
    find_workouts_in_period,
    is_valid_workout_date,
)


def test_valid_date():
    assert is_valid_workout_date(date.today())


def test_future_date_invalid():
    future = date.today() + timedelta(days=1)
    assert not is_valid_workout_date(future)


def test_workout_without_exercises_raises():
    workouts = []
    with pytest.raises(ValueError):
        create_workout(workouts, date.today(), "силовая", [])


def test_create_and_cancel_workout():
    workouts = []
    exercises_done = [{"exercise_id": 1, "sets": 3, "reps": 8, "weight": 80}]
    workout = create_workout(workouts, date.today(), "силовая", exercises_done)
    assert len(workouts) == 1
    cancel_workout(workouts, workout["id"])
    assert len(workouts) == 0


def test_find_workouts_in_period():
    workouts = []
    exercises_done = [{"exercise_id": 1, "sets": 3, "reps": 8, "weight": 80}]
    create_workout(
        workouts, date.today() - timedelta(days=2), "силовая", exercises_done
    )
    create_workout(
        workouts, date.today() - timedelta(days=40), "кардио", exercises_done
    )
    found = find_workouts_in_period(
        workouts, date.today() - timedelta(days=7), date.today()
    )
    assert len(found) == 1
