"""Классы тренировок и функции работы с ними."""

from datetime import date
from typing import Optional

from .exercises import Exercise
from .users import User


class WorkoutExercise:
    """Упражнение, выполненное в тренировке: подходы, повторения, вес."""

    def __init__(self, exercise: Exercise, sets: int, reps: int, weight: float) -> None:
        """Создать запись о выполненном упражнении."""
        self.exercise = exercise
        self.sets = sets
        self.reps = reps
        self.weight = weight

    def is_valid(self) -> bool:
        """Проверить правило: подходы и повторения не меньше нуля."""
        return self.sets >= 0 and self.reps >= 0

    def tonnage(self) -> float:
        """Вернуть тоннаж: подходы × повторения × вес."""
        return self.sets * self.reps * self.weight

    def __str__(self) -> str:
        """Вернуть строковое представление выполненного упражнения."""
        return (
            f"{self.exercise.name}: {self.sets} подх. по {self.reps} раз, "
            f"{self.weight:g} кг"
        )


class Workout:
    """Тренировка пользователя (базовый класс).

    Хранит ссылки на объект User и на выполненные упражнения.
    Тип тренировки задаётся атрибутом класса WORKOUT_TYPE в подклассах.
    """

    WORKOUT_TYPE = "тренировка"

    def __init__(
        self,
        workout_id: int,
        user: User,
        workout_date: date,
        exercises: list[WorkoutExercise],
        duration_min: int = 0,
    ) -> None:
        """Создать объект тренировки."""
        self.id = workout_id
        self.user = user
        self.workout_date = workout_date
        self.exercises = exercises
        self.duration_min = duration_min
        self.is_cancelled = False

    @property
    def workout_type(self) -> str:
        """Вернуть тип тренировки (задаётся классом)."""
        return self.WORKOUT_TYPE

    @staticmethod
    def is_valid_date(workout_date: date) -> bool:
        """Проверить правило: дата тренировки не в будущем."""
        return workout_date <= date.today()

    def cancel(self) -> None:
        """Отменить тренировку: объект остаётся, меняется его состояние."""
        self.is_cancelled = True

    def is_in_period(self, period_start: date, period_end: date) -> bool:
        """Проверить, попадает ли дата тренировки в период (включительно)."""
        return period_start <= self.workout_date <= period_end

    def __str__(self) -> str:
        """Вернуть строковое представление тренировки."""
        status = " [отменена]" if self.is_cancelled else ""
        return (
            f"№{self.id} {self.workout_date:%d.%m.%Y}, {self.workout_type}, "
            f"упражнений: {len(self.exercises)}{status}"
        )


class CardioWorkout(Workout):
    """Кардио-тренировка: в описании важна длительность."""

    WORKOUT_TYPE = "кардио"

    def __str__(self) -> str:
        """Вернуть описание с длительностью тренировки."""
        return f"{super().__str__()}, длительность: {self.duration_min} мин"


class StrengthWorkout(Workout):
    """Силовая тренировка: в описании важен суммарный тоннаж."""

    WORKOUT_TYPE = "силовая"

    def total_tonnage(self) -> float:
        """Вернуть суммарный тоннаж по всем упражнениям тренировки."""
        return sum(item.tonnage() for item in self.exercises)

    def __str__(self) -> str:
        """Вернуть описание с суммарным тоннажем."""
        return f"{super().__str__()}, тоннаж: {self.total_tonnage():g} кг"


WORKOUT_CLASSES: dict[str, type[Workout]] = {
    CardioWorkout.WORKOUT_TYPE: CardioWorkout,
    StrengthWorkout.WORKOUT_TYPE: StrengthWorkout,
}


def normalize_workout_type(raw_type: str) -> str:
    """Привести тип к нижнему регистру; неизвестный тип — ValueError."""
    workout_type = raw_type.strip().lower()
    if workout_type not in WORKOUT_CLASSES:
        allowed = ", ".join(WORKOUT_CLASSES)
        raise ValueError(
            f"Неизвестный тип тренировки «{raw_type}». Допустимы: {allowed}"
        )
    return workout_type


def build_workout(
    workout_id: int,
    user: User,
    workout_date: date,
    workout_type: str,
    exercises: list[WorkoutExercise],
    duration_min: int = 0,
) -> Workout:
    """Создать тренировку нужного подкласса по её типу."""
    workout_class = WORKOUT_CLASSES[normalize_workout_type(workout_type)]
    return workout_class(workout_id, user, workout_date, exercises, duration_min)


def _validate_exercises_done(exercises_done: list[WorkoutExercise]) -> None:
    """Проверить бизнес-правила по выполненным упражнениям."""
    if not exercises_done:
        raise ValueError(
            "Тренировка не может быть создана без хотя бы одного упражнения"
        )
    if not all(item.is_valid() for item in exercises_done):
        raise ValueError("Количество подходов и повторений должно быть >= 0")


def create_workout(
    workouts: list[Workout],
    user: User,
    workout_date: date,
    workout_type: str,
    exercises_done: list[WorkoutExercise],
    duration_min: int = 0,
) -> Workout:
    """Создать тренировку пользователя и добавить её в коллекцию."""
    workout_type = normalize_workout_type(workout_type)
    if not Workout.is_valid_date(workout_date):
        raise ValueError("Дата тренировки не может быть в будущем")
    _validate_exercises_done(exercises_done)

    new_id = max((w.id for w in workouts), default=0) + 1
    workout = build_workout(
        new_id, user, workout_date, workout_type, exercises_done, duration_min
    )
    workouts.append(workout)
    return workout


def find_workout_by_id(workouts: list[Workout], workout_id: int) -> Optional[Workout]:
    """Найти тренировку по id или вернуть None."""
    for workout in workouts:
        if workout.id == workout_id:
            return workout
    return None


def get_user_workouts(workouts: list[Workout], user: User) -> list[Workout]:
    """Вернуть все тренировки пользователя, включая отменённые."""
    return [workout for workout in workouts if workout.user is user]


def cancel_workout(workouts: list[Workout], workout_id: int) -> bool:
    """Отменить тренировку по id, не удаляя её из коллекции.

    Возвращает False, если тренировка уже была отменена.
    Если тренировки с таким id нет, вызывает ValueError.
    """
    workout = find_workout_by_id(workouts, workout_id)
    if workout is None:
        raise ValueError(f"Тренировка с id={workout_id} не найдена")
    if workout.is_cancelled:
        return False
    workout.cancel()
    return True


def find_workouts_in_period(
    workouts: list[Workout],
    user: User,
    period_start: date,
    period_end: date,
) -> list[Workout]:
    """Отобрать активные тренировки пользователя за период."""
    return [
        workout
        for workout in workouts
        if workout.user is user
        and not workout.is_cancelled
        and workout.is_in_period(period_start, period_end)
    ]


def get_workout_stats(workouts: list[Workout]) -> dict:
    """Посчитать статистику по тренировкам; отменённые не учитываются."""
    active = [workout for workout in workouts if not workout.is_cancelled]
    by_type: dict[str, int] = {}
    for workout in active:
        by_type[workout.workout_type] = by_type.get(workout.workout_type, 0) + 1
    return {
        "total_workouts": len(active),
        "total_duration_min": sum(w.duration_min for w in active),
        "by_type": by_type,
    }


def show_workouts(workouts: list[Workout]) -> None:
    """Вывести список тренировок."""
    if not workouts:
        print("Тренировок пока нет")
        return
    for workout in workouts:
        print(workout)


def reality_task(task_done: int, exercises_done: list[WorkoutExercise]) -> int:
    """Функция из ПР1: итоговое число выполненных упражнений."""
    return task_done + len(exercises_done)


def trening_result(
    result: bool, task_done: int, exercises_done: list[WorkoutExercise]
) -> str:
    """Функция из ПР1: текст о результате тренировки."""
    if result:
        done = reality_task(task_done, exercises_done)
        return "Тренировка выполнена! " f"Количество сделанных упражнений = {done}"
    return "Ты лентяй!!!"
