"""Функции для работы со справочником упражнений."""


def add_exercise(exercises: dict[int, dict], name: str, muscle_group: str) -> int:
    """Добавить упражнение в справочник exercises.

    Возвращает id нового упражнения.
    """
    new_id = max(exercises.keys(), default=0) + 1
    exercises[new_id] = {"name": name, "muscle_group": muscle_group}
    return new_id


def find_exercise(exercises: dict[int, dict], query: str) -> dict[int, dict]:
    """Найти упражнения, в названии которых встречается query."""
    query_lower = query.lower()
    return {
        exercise_id: data
        for exercise_id, data in exercises.items()
        if query_lower in data["name"].lower()
    }


def filter_exercises_by_muscle_group(
    exercises: dict[int, dict], muscle_group: str
) -> dict[int, dict]:
    """Отобрать упражнения по рабочей группе мышц."""
    return {
        exercise_id: data
        for exercise_id, data in exercises.items()
        if data["muscle_group"].lower() == muscle_group.lower()
    }


def sort_exercises(exercises: dict[int, dict]) -> list[tuple[int, dict]]:
    """Вернуть упражнения, отсортированные по названию."""
    return sorted(exercises.items(), key=lambda item: item[1]["name"])
