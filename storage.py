"""Загрузка и сохранение данных проекта в JSON-файлах.

В JSON хранятся только данные и идентификаторы связанных объектов.
Преобразование JSON <-> объекты выполняется в этом модуле.
"""

import json
from datetime import date
from pathlib import Path

from models import Exercise, Result, User, Workout, WorkoutExercise
from models.exercises import find_exercise_by_id
from models.users import find_user_by_id
from models.workouts import build_workout, find_workout_by_id


def _read_records(filename: str) -> list[dict]:
    """Прочитать список записей из JSON-файла.

    Нет файла — пустой список. Повреждённый файл — предупреждение
    и пустой список.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Предупреждение: файл {filename} повреждён, данные не загружены")
        return []
    if not isinstance(data, list):
        print(f"Предупреждение: в файле {filename} ожидался список записей")
        return []
    records = []
    for record in data:
        if isinstance(record, dict):
            records.append(record)
        else:
            print(f"Предупреждение: запись в {filename} пропущена: {record!r}")
    return records


def _write_records(filename: str, records: list[dict]) -> None:
    """Записать список записей в JSON-файл."""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def _warn_skipped(kind: str, record: dict, error: Exception) -> None:
    """Вывести предупреждение о пропущенной записи."""
    print(f"Предупреждение: {kind} {record.get('id', '?')} пропущена: {error}")


def load_exercises(filename: str) -> list[Exercise]:
    """Загрузить упражнения из JSON-файла в список объектов Exercise."""
    exercises = []
    for record in _read_records(filename):
        try:
            exercises.append(
                Exercise(record["id"], record["name"], record["muscle_group"])
            )
        except KeyError as error:
            _warn_skipped("запись упражнения", record, error)
    return exercises


def save_exercises(filename: str, exercises: list[Exercise]) -> None:
    """Сохранить объекты Exercise в JSON-файл."""
    _write_records(
        filename,
        [
            {"id": e.id, "name": e.name, "muscle_group": e.muscle_group}
            for e in exercises
        ],
    )


def load_users(filename: str) -> list[User]:
    """Загрузить пользователей из JSON-файла в список объектов User."""
    users = []
    for record in _read_records(filename):
        try:
            users.append(User.from_data(record))
        except (KeyError, ValueError, TypeError) as error:
            _warn_skipped("запись пользователя", record, error)
    return users


def save_users(filename: str, users: list[User]) -> None:
    """Сохранить объекты User в JSON-файл."""
    _write_records(
        filename,
        [
            {
                "id": u.id,
                "name": u.name,
                "registered_at": u.registered_at.isoformat(),
            }
            for u in users
        ],
    )


def _workout_from_record(
    record: dict, users: list[User], exercises: list[Exercise]
) -> Workout:
    """Восстановить объект тренировки из записи JSON и связанных объектов."""
    user = find_user_by_id(users, record["user_id"])
    if user is None:
        raise ValueError(f"пользователь {record['user_id']} не найден")

    items = []
    for item in record["exercises"]:
        exercise = find_exercise_by_id(exercises, item["exercise_id"])
        if exercise is None:
            raise ValueError(f"упражнение {item['exercise_id']} не найдено")
        items.append(
            WorkoutExercise(exercise, item["sets"], item["reps"], item["weight"])
        )

    workout = build_workout(
        record["id"],
        user,
        date.fromisoformat(record["date"]),
        record["type"],
        items,
        record.get("duration_min", 0),
    )
    workout.is_cancelled = record.get("is_cancelled", False)
    return workout


def load_workouts(
    filename: str, users: list[User], exercises: list[Exercise]
) -> list[Workout]:
    """Загрузить тренировки и восстановить связи с User и Exercise.

    Запись с отсутствующим пользователем или упражнением пропускается
    с предупреждением: корректный объект из неё не создаётся.
    """
    workouts = []
    for record in _read_records(filename):
        try:
            workouts.append(_workout_from_record(record, users, exercises))
        except (KeyError, ValueError, TypeError) as error:
            _warn_skipped("тренировка", record, error)
    return workouts


def save_workouts(filename: str, workouts: list[Workout]) -> None:
    """Сохранить тренировки в JSON: связи записываются как id."""
    _write_records(
        filename,
        [
            {
                "id": w.id,
                "user_id": w.user.id,
                "date": w.workout_date.isoformat(),
                "type": w.workout_type,
                "duration_min": w.duration_min,
                "exercises": [
                    {
                        "exercise_id": item.exercise.id,
                        "sets": item.sets,
                        "reps": item.reps,
                        "weight": item.weight,
                    }
                    for item in w.exercises
                ],
                "is_cancelled": w.is_cancelled,
            }
            for w in workouts
        ],
    )


def _result_from_record(
    record: dict, users: list[User], workouts: list[Workout]
) -> Result:
    """Восстановить объект результата из записи JSON и связанных объектов."""
    user = find_user_by_id(users, record["user_id"])
    if user is None:
        raise ValueError(f"пользователь {record['user_id']} не найден")

    period_workouts = []
    for workout_id in record["workout_ids"]:
        workout = find_workout_by_id(workouts, workout_id)
        if workout is None:
            raise ValueError(f"тренировка {workout_id} не найдена")
        period_workouts.append(workout)

    return Result(
        record["id"],
        user,
        date.fromisoformat(record["period_start"]),
        date.fromisoformat(record["period_end"]),
        period_workouts,
    )


def load_results(
    filename: str, users: list[User], workouts: list[Workout]
) -> list[Result]:
    """Загрузить результаты за периоды и восстановить связи с User и Workout."""
    results = []
    for record in _read_records(filename):
        try:
            results.append(_result_from_record(record, users, workouts))
        except (KeyError, ValueError, TypeError) as error:
            _warn_skipped("результат", record, error)
    return results


def save_results(filename: str, results: list[Result]) -> None:
    """Сохранить результаты за периоды в JSON: связи записываются как id."""
    _write_records(
        filename,
        [
            {
                "id": r.id,
                "user_id": r.user.id,
                "period_start": r.period_start.isoformat(),
                "period_end": r.period_end.isoformat(),
                "workout_ids": [w.id for w in r.workouts],
            }
            for r in results
        ],
    )
