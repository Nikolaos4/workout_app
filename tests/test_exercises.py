"""Тесты класса Exercise и функций работы с упражнениями."""

import pytest

from models import Exercise
from models.exercises import (
    add_exercise,
    filter_exercises_by_muscle_group,
    find_exercise,
    find_exercise_by_id,
    sort_exercises,
)


def test_exercise_creation():
    exercise = Exercise(1, "Жим лёжа", "Грудь")
    assert exercise.id == 1
    assert exercise.name == "Жим лёжа"
    assert exercise.muscle_group == "Грудь"


def test_exercise_str():
    assert str(Exercise(1, "Жим лёжа", "Грудь")) == "Жим лёжа (Грудь)"


def test_exercise_is_for_muscle_group():
    exercise = Exercise(1, "Присед", "Ноги")
    assert exercise.is_for_muscle_group("ноги")
    assert not exercise.is_for_muscle_group("Грудь")


def test_add_exercise_returns_object_and_adds_to_collection():
    exercises = []
    exercise = add_exercise(exercises, "Жим лёжа", "Грудь")
    assert isinstance(exercise, Exercise)
    assert exercises == [exercise]
    assert exercise.id == 1


def test_add_exercise_increments_id():
    exercises = []
    add_exercise(exercises, "Жим лёжа", "Грудь")
    second = add_exercise(exercises, "Присед", "Ноги")
    assert second.id == 2


def test_add_exercise_empty_name_raises():
    with pytest.raises(ValueError):
        add_exercise([], "  ", "Грудь")


def test_find_exercise():
    exercises = []
    add_exercise(exercises, "Жим лёжа", "Грудь")
    add_exercise(exercises, "Присед", "Ноги")
    found = find_exercise(exercises, "жим")
    assert [e.name for e in found] == ["Жим лёжа"]


def test_find_exercise_by_id():
    exercises = []
    exercise = add_exercise(exercises, "Присед", "Ноги")
    assert find_exercise_by_id(exercises, 1) is exercise
    assert find_exercise_by_id(exercises, 99) is None


def test_filter_exercises_by_muscle_group():
    exercises = []
    add_exercise(exercises, "Присед", "Ноги")
    add_exercise(exercises, "Жим лёжа", "Грудь")
    result = filter_exercises_by_muscle_group(exercises, "Ноги")
    assert len(result) == 1
    assert result[0].name == "Присед"


def test_sort_exercises_by_name():
    exercises = []
    add_exercise(exercises, "Присед", "Ноги")
    add_exercise(exercises, "Жим лёжа", "Грудь")
    assert [e.name for e in sort_exercises(exercises)] == [
        "Жим лёжа",
        "Присед",
    ]
