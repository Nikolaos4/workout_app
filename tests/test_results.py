"""Тесты класса Result и функций работы с результатами за период."""

from datetime import date, timedelta

import pytest

from models import Exercise, Result, User, WorkoutExercise
from models.results import (
    create_result,
    find_result_by_id,
    get_user_results,
)
from models.workouts import cancel_workout, create_workout


def make_user(user_id: int = 1) -> User:
    return User(user_id, f"Пользователь {user_id}", date(2026, 9, 1))


def make_items() -> list[WorkoutExercise]:
    return [WorkoutExercise(Exercise(1, "Жим лёжа", "Грудь"), 3, 8, 80)]


def days_ago(days: int) -> date:
    return date.today() - timedelta(days=days)


def make_workouts(user: User) -> list:
    workouts = []
    create_workout(workouts, user, days_ago(5), "силовая", make_items(), 60)
    create_workout(workouts, user, days_ago(20), "кардио", make_items(), 30)
    return workouts


def test_create_result_holds_references():
    user = make_user()
    workouts = make_workouts(user)
    results = []
    result = create_result(results, workouts, user, days_ago(30), date.today())
    assert isinstance(result, Result)
    assert result.user is user
    assert result.workouts == workouts
    assert results == [result]


def test_create_result_includes_only_workouts_in_period():
    user = make_user()
    workouts = make_workouts(user)
    result = create_result([], workouts, user, days_ago(7), date.today())
    assert len(result.workouts) == 1
    assert result.workouts[0] is workouts[0]


def test_create_result_uses_only_workouts_of_user():
    user, other = make_user(1), make_user(2)
    workouts = make_workouts(user)
    result = create_result([], workouts, other, days_ago(30), date.today())
    assert result.workouts == []


def test_create_result_invalid_period_raises():
    with pytest.raises(ValueError):
        create_result([], [], make_user(), date.today(), days_ago(1))


def test_find_result_by_id():
    user = make_user()
    results = []
    result = create_result(results, [], user, days_ago(30), date.today())
    assert find_result_by_id(results, result.id) is result
    with pytest.raises(ValueError):
        find_result_by_id(results, 99)


def test_get_user_results_filters_by_user():
    results = []
    first, second = make_user(1), make_user(2)
    create_result(results, [], first, days_ago(30), date.today())
    create_result(results, [], second, days_ago(30), date.today())
    assert len(get_user_results(results, first)) == 1


def test_result_get_stats():
    user = make_user()
    workouts = make_workouts(user)
    result = create_result([], workouts, user, days_ago(30), date.today())
    stats = result.get_stats()
    assert stats["total_workouts"] == 2
    assert stats["total_duration_min"] == 90


def test_result_stats_ignore_workout_cancelled_later():
    user = make_user()
    workouts = make_workouts(user)
    result = create_result([], workouts, user, days_ago(30), date.today())
    cancel_workout(workouts, workouts[0].id)
    assert result.get_stats()["total_workouts"] == 1


def test_result_str():
    user = make_user()
    workouts = make_workouts(user)
    result = create_result([], workouts, user, days_ago(30), date.today())
    assert "Пользователь 1" in str(result)
    assert "тренировок: 2" in str(result)
