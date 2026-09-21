"""Тесты функций работы со справочником упражнений."""

from exercises import (
    add_exercise,
    filter_exercises_by_muscle_group,
    find_exercise,
)


def test_add_exercise():
    exercises = {}
    add_exercise(exercises, "Жим лёжа", "Грудь")
    assert len(exercises) == 1


def test_find_exercise():
    exercises = {}
    add_exercise(exercises, "Жим лёжа", "Грудь")
    assert find_exercise(exercises, "жим")


def test_filter_exercises_by_muscle_group():
    exercises = {}
    add_exercise(exercises, "Присед", "Ноги")
    add_exercise(exercises, "Жим лёжа", "Грудь")
    result = filter_exercises_by_muscle_group(exercises, "Ноги")
    assert len(result) == 1
