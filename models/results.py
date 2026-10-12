"""Класс Result («Результат за период времени») и функции работы с ним."""

from datetime import date

from .users import User
from .workouts import Workout, find_workouts_in_period, get_workout_stats


class Result:
    """Результат пользователя за период: ссылки на тренировки периода."""

    def __init__(
        self,
        result_id: int,
        user: User,
        period_start: date,
        period_end: date,
        workouts: list[Workout],
    ) -> None:
        """Создать объект результата за период."""
        self.id = result_id
        self.user = user
        self.period_start = period_start
        self.period_end = period_end
        self.workouts = workouts

    def get_stats(self) -> dict:
        """Посчитать статистику по тренировкам результата.

        Отменённые тренировки не учитываются, даже если отмена
        произошла уже после формирования результата.
        """
        return get_workout_stats(self.workouts)

    def __str__(self) -> str:
        """Вернуть строковое представление результата."""
        stats = self.get_stats()
        return (
            f"Результат №{self.id}: {self.user.name}, "
            f"{self.period_start:%d.%m.%Y} — {self.period_end:%d.%m.%Y}, "
            f"тренировок: {stats['total_workouts']}"
        )


def create_result(
    results: list[Result],
    workouts: list[Workout],
    user: User,
    period_start: date,
    period_end: date,
) -> Result:
    """Сформировать результат пользователя за период и добавить в коллекцию."""
    if period_end < period_start:
        raise ValueError("Дата окончания периода не может быть раньше даты начала")
    period_workouts = find_workouts_in_period(workouts, user, period_start, period_end)
    new_id = max((r.id for r in results), default=0) + 1
    result = Result(new_id, user, period_start, period_end, period_workouts)
    results.append(result)
    return result


def find_result_by_id(results: list[Result], result_id: int) -> Result:
    """Найти результат по id; если его нет, вызвать ValueError."""
    for result in results:
        if result.id == result_id:
            return result
    raise ValueError(f"Результат с id={result_id} не найден")


def get_user_results(results: list[Result], user: User) -> list[Result]:
    """Вернуть результаты пользователя."""
    return [result for result in results if result.user is user]


def show_results(results: list[Result]) -> None:
    """Вывести список результатов."""
    if not results:
        print("Результатов пока нет")
        return
    for result in results:
        print(result)
