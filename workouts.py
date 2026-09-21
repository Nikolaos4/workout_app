"""Функции для работы с тренировками."""

from datetime import date


def is_valid_workout_date(workout_date: date) -> bool:
    """Проверить, что дата тренировки не в будущем."""
    return workout_date <= date.today()


def _validate_exercises_done(exercises_done: list[dict]) -> None:
    """Проверить бизнес-правила по списку выполненных упражнений."""
    if not exercises_done:
        raise ValueError(
            "Тренировка не может быть создана без хотя бы одного " "упражнения"
        )
    for item in exercises_done:
        if item.get("sets", 0) < 0 or item.get("reps", 0) < 0:
            raise ValueError("Количество подходов и повторений должно быть >= 0")


def create_workout(
    workouts: list[dict],
    workout_date: date,
    workout_type: str,
    exercises_done: list[dict],
    duration_min: int = 0,
) -> dict:
    """Создать тренировку и добавить её в список workouts."""
    if not is_valid_workout_date(workout_date):
        raise ValueError("Дата тренировки не может быть в будущем")
    _validate_exercises_done(exercises_done)

    new_id = max((w["id"] for w in workouts), default=0) + 1
    workout = {
        "id": new_id,
        "date": workout_date.isoformat(),
        "type": workout_type,
        "duration_min": duration_min,
        "exercises": exercises_done,
    }
    workouts.append(workout)
    return workout


def cancel_workout(workouts: list[dict], workout_id: int) -> None:
    """Удалить тренировку по id."""
    for i, workout in enumerate(workouts):
        if workout["id"] == workout_id:
            del workouts[i]
            return
    raise ValueError(f"Тренировка с id={workout_id} не найдена")


def find_workouts_in_period(
    workouts: list[dict], period_start: date, period_end: date
) -> list[dict]:
    """Отобрать тренировки, дата которых попадает в период [start, end]."""
    result = []
    for workout in workouts:
        workout_date = date.fromisoformat(workout["date"])
        if period_start <= workout_date <= period_end:
            result.append(workout)
    return result


def get_workout_stats(workouts: list[dict]) -> dict:
    """Посчитать статистику по тренировкам."""
    total_duration = sum(w["duration_min"] for w in workouts)
    by_type: dict[str, int] = {}
    for w in workouts:
        by_type[w["type"]] = by_type.get(w["type"], 0) + 1
    return {
        "total_workouts": len(workouts),
        "total_duration_min": total_duration,
        "by_type": by_type,
    }


def reality_task(task_done: int, exercises_done: list[dict]) -> int:
    """Перенесённая из ПР1 функция Reality_task.

    Считает итоговое количество выполненных упражнений по факту
    переданного списка (в ПР1 функция игнорировала аргумент и всегда
    возвращала 3 — здесь эта ошибка исправлена).
    """
    return task_done + len(exercises_done)


def trening_result(result: bool, task_done: int, exercises_done: list[dict]) -> str:
    """Перенесённая из ПР1 функция trening_result.

    В ПР1 функция сразу печатала результат (print); теперь возвращает
    строку — это правильнее, так как вывод и логика разделены.
    """
    if result:
        done = reality_task(task_done, exercises_done)
        return f"Тренировка выполнена! Количество сделанных " f"упражнений = {done}"
    return "Ты лентяй!!!"
