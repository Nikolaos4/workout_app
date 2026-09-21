"""Тесты функций работы с результатами за период времени."""

from datetime import date, timedelta

import pytest

from results import create_result, find_result_by_id, get_result_stats
from workouts import create_workout


def _make_workouts() -> list[dict]:
    """Вспомогательная функция: подготовить тестовый список тренировок."""
    workouts: list[dict] = []
    exercises_done = [{"exercise_id": 1, "sets": 3, "reps": 8, "weight": 80}]
    create_workout(
        workouts,
        date.today() - timedelta(days=5),
        "силовая",
        exercises_done,
        duration_min=60,
    )
    create_workout(
        workouts,
        date.today() - timedelta(days=20),
        "кардио",
        exercises_done,
        duration_min=30,
    )
    return workouts


def test_create_result_includes_only_workouts_in_period():
    workouts = _make_workouts()
    results: list[dict] = []
    result = create_result(
        results,
        workouts,
        date.today() - timedelta(days=7),
        date.today(),
    )
    assert len(result["workout_ids"]) == 1


def test_create_result_invalid_period_raises():
    results: list[dict] = []
    with pytest.raises(ValueError):
        create_result(results, [], date.today(), date.today() - timedelta(days=1))


def test_find_result_by_id():
    workouts = _make_workouts()
    results: list[dict] = []
    result = create_result(
        results,
        workouts,
        date.today() - timedelta(days=30),
        date.today(),
    )
    found = find_result_by_id(results, result["id"])
    assert found is result


def test_get_result_stats():
    workouts = _make_workouts()
    results: list[dict] = []
    result = create_result(
        results,
        workouts,
        date.today() - timedelta(days=30),
        date.today(),
    )
    stats = get_result_stats(result, workouts)
    assert stats["total_workouts"] == 2
    assert stats["total_duration_min"] == 90
