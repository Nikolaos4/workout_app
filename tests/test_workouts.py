"""Тесты классов тренировок и функций работы с ними."""

from datetime import date, timedelta

import pytest

from models import (
    CardioWorkout,
    Exercise,
    StrengthWorkout,
    User,
    Workout,
    WorkoutExercise,
)
from models.workouts import (
    cancel_workout,
    create_workout,
    find_workout_by_id,
    find_workouts_in_period,
    get_user_workouts,
    get_workout_stats,
    normalize_workout_type,
    reality_task,
    trening_result,
)


def make_user(user_id: int = 1) -> User:
    return User(user_id, f"Пользователь {user_id}", date(2026, 9, 1))


def make_items() -> list[WorkoutExercise]:
    return [WorkoutExercise(Exercise(1, "Жим лёжа", "Грудь"), 3, 8, 80)]


def days_ago(days: int) -> date:
    return date.today() - timedelta(days=days)


def test_workout_exercise_attributes_and_methods():
    item = WorkoutExercise(Exercise(1, "Жим лёжа", "Грудь"), 3, 8, 80)
    assert item.sets == 3
    assert item.is_valid()
    assert item.tonnage() == 3 * 8 * 80
    assert str(item) == "Жим лёжа: 3 подх. по 8 раз, 80 кг"


def test_workout_exercise_negative_values_invalid():
    exercise = Exercise(1, "Жим лёжа", "Грудь")
    assert not WorkoutExercise(exercise, -1, 8, 80).is_valid()
    assert not WorkoutExercise(exercise, 3, -1, 80).is_valid()


def test_is_valid_date_static_method():
    assert Workout.is_valid_date(date.today())
    assert not Workout.is_valid_date(date.today() + timedelta(days=1))


def test_normalize_workout_type():
    assert normalize_workout_type("  Кардио ") == "кардио"
    assert normalize_workout_type("СИЛОВАЯ") == "силовая"
    with pytest.raises(ValueError):
        normalize_workout_type("йога")


def test_create_workout_selects_subclass_by_type():
    workouts = []
    user = make_user()
    strength = create_workout(workouts, user, days_ago(1), "силовая", make_items())
    cardio = create_workout(workouts, user, days_ago(1), " Кардио ", make_items())
    assert isinstance(strength, StrengthWorkout)
    assert isinstance(cardio, CardioWorkout)
    assert isinstance(strength, Workout)
    assert len(workouts) == 2
    assert cardio.workout_type == "кардио"


def test_workout_holds_references_to_objects():
    user = make_user()
    items = make_items()
    workout = create_workout([], user, days_ago(1), "силовая", items)
    assert workout.user is user
    assert workout.exercises[0].exercise is items[0].exercise


def test_create_workout_unknown_type_raises():
    with pytest.raises(ValueError):
        create_workout([], make_user(), days_ago(1), "йога", make_items())


def test_create_workout_future_date_raises():
    future = date.today() + timedelta(days=1)
    with pytest.raises(ValueError):
        create_workout([], make_user(), future, "силовая", make_items())


def test_create_workout_without_exercises_raises():
    with pytest.raises(ValueError):
        create_workout([], make_user(), days_ago(1), "силовая", [])


def test_create_workout_negative_sets_raises():
    items = [WorkoutExercise(Exercise(1, "Жим лёжа", "Грудь"), -1, 8, 80)]
    with pytest.raises(ValueError):
        create_workout([], make_user(), days_ago(1), "силовая", items)


def test_failed_create_does_not_change_collection():
    workouts = []
    with pytest.raises(ValueError):
        create_workout(workouts, make_user(), days_ago(1), "силовая", [])
    assert workouts == []


def test_str_differs_by_subclass():
    user = make_user()
    strength = create_workout([], user, days_ago(1), "силовая", make_items())
    cardio = create_workout([], user, days_ago(1), "кардио", make_items(), 45)
    assert "тоннаж: 1920 кг" in str(strength)
    assert "длительность: 45 мин" in str(cardio)


def test_cancel_keeps_object_in_collection():
    workouts = []
    workout = create_workout(
        workouts, make_user(), days_ago(1), "силовая", make_items()
    )
    assert cancel_workout(workouts, workout.id) is True
    assert len(workouts) == 1
    assert workout.is_cancelled
    assert "[отменена]" in str(workout)


def test_cancel_twice_returns_false():
    workouts = []
    workout = create_workout(
        workouts, make_user(), days_ago(1), "силовая", make_items()
    )
    cancel_workout(workouts, workout.id)
    assert cancel_workout(workouts, workout.id) is False


def test_cancel_unknown_workout_raises():
    with pytest.raises(ValueError):
        cancel_workout([], 1)


def test_cancelled_id_is_not_reused():
    workouts = []
    user = make_user()
    first = create_workout(workouts, user, days_ago(1), "силовая", make_items())
    cancel_workout(workouts, first.id)
    second = create_workout(workouts, user, days_ago(1), "силовая", make_items())
    assert second.id == first.id + 1


def test_find_workout_by_id():
    workouts = []
    workout = create_workout(
        workouts, make_user(), days_ago(1), "силовая", make_items()
    )
    assert find_workout_by_id(workouts, workout.id) is workout
    assert find_workout_by_id(workouts, 99) is None


def test_get_user_workouts_filters_by_user():
    workouts = []
    first, second = make_user(1), make_user(2)
    create_workout(workouts, first, days_ago(1), "силовая", make_items())
    create_workout(workouts, second, days_ago(1), "кардио", make_items())
    assert len(get_user_workouts(workouts, first)) == 1


def test_find_workouts_in_period_filters_user_period_and_cancelled():
    workouts = []
    user, other = make_user(1), make_user(2)
    inside = create_workout(workouts, user, days_ago(2), "силовая", make_items())
    create_workout(workouts, user, days_ago(40), "кардио", make_items())
    create_workout(workouts, other, days_ago(2), "кардио", make_items())
    cancelled = create_workout(workouts, user, days_ago(3), "кардио", make_items())
    cancel_workout(workouts, cancelled.id)

    found = find_workouts_in_period(workouts, user, days_ago(7), date.today())
    assert found == [inside]


def test_get_workout_stats_ignores_cancelled():
    workouts = []
    user = make_user()
    create_workout(workouts, user, days_ago(1), "силовая", make_items(), 60)
    cancelled = create_workout(workouts, user, days_ago(2), "кардио", make_items(), 30)
    cancel_workout(workouts, cancelled.id)
    stats = get_workout_stats(workouts)
    assert stats["total_workouts"] == 1
    assert stats["total_duration_min"] == 60
    assert stats["by_type"] == {"силовая": 1}


def test_reality_task_counts_exercises():
    assert reality_task(0, make_items() * 3) == 3


def test_trening_result_messages():
    assert "= 1" in trening_result(True, 0, make_items())
    assert trening_result(False, 0, []) == "Ты лентяй!!!"
