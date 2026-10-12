"""Класс Exercise и функции работы со справочником упражнений."""

from typing import Optional


class Exercise:
    """Упражнение из справочника."""

    def __init__(self, exercise_id: int, name: str, muscle_group: str) -> None:
        """Создать объект упражнения."""
        self.id = exercise_id
        self.name = name
        self.muscle_group = muscle_group

    def is_for_muscle_group(self, muscle_group: str) -> bool:
        """Проверить, относится ли упражнение к указанной группе мышц."""
        return self.muscle_group.lower() == muscle_group.strip().lower()

    def __str__(self) -> str:
        """Вернуть строковое представление упражнения."""
        return f"{self.name} ({self.muscle_group})"


def add_exercise(exercises: list[Exercise], name: str, muscle_group: str) -> Exercise:
    """Создать упражнение, добавить его в справочник и вернуть."""
    name = name.strip()
    muscle_group = muscle_group.strip()
    if not name or not muscle_group:
        raise ValueError("Название и группа мышц не могут быть пустыми")
    new_id = max((exercise.id for exercise in exercises), default=0) + 1
    exercise = Exercise(new_id, name, muscle_group)
    exercises.append(exercise)
    return exercise


def find_exercise(exercises: list[Exercise], query: str) -> list[Exercise]:
    """Найти упражнения, в названии которых встречается подстрока query."""
    query_lower = query.strip().lower()
    return [e for e in exercises if query_lower in e.name.lower()]


def find_exercise_by_id(
    exercises: list[Exercise], exercise_id: int
) -> Optional[Exercise]:
    """Найти упражнение по id или вернуть None."""
    for exercise in exercises:
        if exercise.id == exercise_id:
            return exercise
    return None


def filter_exercises_by_muscle_group(
    exercises: list[Exercise], muscle_group: str
) -> list[Exercise]:
    """Отобрать упражнения по рабочей группе мышц."""
    return [e for e in exercises if e.is_for_muscle_group(muscle_group)]


def sort_exercises(exercises: list[Exercise]) -> list[Exercise]:
    """Вернуть упражнения, отсортированные по названию."""
    return sorted(exercises, key=lambda exercise: exercise.name.lower())


def show_exercises(exercises: list[Exercise]) -> None:
    """Вывести список упражнений."""
    if not exercises:
        print("Упражнения не найдены")
        return
    for exercise in sort_exercises(exercises):
        print(f"{exercise.id}. {exercise}")
