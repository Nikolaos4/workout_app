"""Функции сохранения и загрузки данных проекта."""

import json


def load_exercises(filename: str) -> dict[int, dict]:
    """Загрузить справочник упражнений из JSON-файла."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, справочник будет пустым")
        return {}
    return {
        item["id"]: {
            "name": item["name"],
            "muscle_group": item["muscle_group"],
        }
        for item in data
    }


def save_exercises(filename: str, exercises: dict[int, dict]) -> None:
    """Сохранить справочник упражнений в JSON-файл."""
    data = [
        {
            "id": exercise_id,
            "name": v["name"],
            "muscle_group": v["muscle_group"],
        }
        for exercise_id, v in exercises.items()
    ]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_workouts(filename: str) -> list[dict]:
    """Загрузить список тренировок из JSON-файла."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, список тренировок будет пуст")
        return []


def save_workouts(filename: str, workouts: list[dict]) -> None:
    """Сохранить список тренировок в JSON-файл."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(workouts, f, ensure_ascii=False, indent=2)


def load_results(filename: str) -> list[dict]:
    """Загрузить список результатов за периоды из JSON-файла."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, список результатов будет пуст")
        return []


def save_results(filename: str, results: list[dict]) -> None:
    """Сохранить список результатов за периоды в JSON-файл."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
