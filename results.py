"""Функции для работы с сущностью «Результат за период времени».

Результат — это агрегат тренировок пользователя за выбранный период
(ID, ID пользователя, период, список ID тренировок), который позволяет
пользователю просматривать свой прогресс за это время (см. роль
«Пользователь: ... просматривать результат за какой-то период»
в описании предметной области ПР1).
"""

from datetime import date

from workouts import find_workouts_in_period, get_workout_stats


def create_result(
    results: list[dict],
    workouts: list[dict],
    period_start: date,
    period_end: date,
    user_id: int = 1,
) -> dict:
    """Сформировать результат пользователя за период и добавить в results.

    Внутри периода отбираются тренировки пользователя (по датам) и их id
    сохраняются в результате — это и есть связь «один результат может
    включать множество тренировок» из предметной области.
    """
    if period_end < period_start:
        raise ValueError("Дата окончания периода не может быть раньше даты начала")

    period_workouts = find_workouts_in_period(workouts, period_start, period_end)
    new_id = max((r["id"] for r in results), default=0) + 1
    result = {
        "id": new_id,
        "user_id": user_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "workout_ids": [w["id"] for w in period_workouts],
    }
    results.append(result)
    return result


def find_result_by_id(results: list[dict], result_id: int) -> dict:
    """Найти результат по id."""
    for result in results:
        if result["id"] == result_id:
            return result
    raise ValueError(f"Результат с id={result_id} не найден")


def get_result_stats(result: dict, workouts: list[dict]) -> dict:
    """Посчитать статистику по тренировкам, входящим в результат."""
    matched_workouts = [w for w in workouts if w["id"] in result["workout_ids"]]
    return get_workout_stats(matched_workouts)
