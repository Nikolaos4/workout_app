"""Точка запуска приложения «Сервис учета тренировок»."""

from exercises import (
    add_exercise,
    filter_exercises_by_muscle_group,
    find_exercise,
    sort_exercises,
)
from results import create_result, find_result_by_id, get_result_stats
from storage import (
    load_exercises,
    load_results,
    load_workouts,
    save_exercises,
    save_results,
    save_workouts,
)
from utils import input_date, input_int
from workouts import (
    cancel_workout,
    create_workout,
    get_workout_stats,
    trening_result,
)

EXERCISES_FILE = "data/exercises.json"
WORKOUTS_FILE = "data/workouts.json"
RESULTS_FILE = "data/results.json"


def show_exercises(exercises: dict[int, dict]) -> None:
    """Вывести список упражнений."""
    if not exercises:
        print("Справочник упражнений пуст")
        return
    for exercise_id, data in sort_exercises(exercises):
        print(f"{exercise_id}. {data['name']} ({data['muscle_group']})")


def show_workouts(workouts: list[dict]) -> None:
    """Вывести список тренировок."""
    if not workouts:
        print("Тренировок пока нет")
        return
    for w in workouts:
        print(
            f"{w['id']}. {w['date']} — {w['type']}, "
            f"{w['duration_min']} мин, упражнений: {len(w['exercises'])}"
        )


def add_exercise_menu(exercises: dict[int, dict]) -> None:
    """Пункт меню: добавить упражнение в справочник."""
    name = input("Название упражнения: ")
    muscle_group = input("Рабочая группа мышц: ")
    add_exercise(exercises, name, muscle_group)
    save_exercises(EXERCISES_FILE, exercises)
    print("Упражнение добавлено")


def find_exercise_menu(exercises: dict[int, dict]) -> None:
    """Пункт меню: найти упражнение по подстроке названия."""
    query = input("Подстрока для поиска: ")
    show_exercises(find_exercise(exercises, query))


def filter_exercise_menu(exercises: dict[int, dict]) -> None:
    """Пункт меню: отфильтровать упражнения по группе мышц."""
    muscle_group = input("Группа мышц: ")
    show_exercises(filter_exercises_by_muscle_group(exercises, muscle_group))


def add_workout_menu(workouts: list[dict], exercises: dict[int, dict]) -> None:
    """Пункт меню: добавить тренировку."""
    if not exercises:
        print("Сначала добавьте хотя бы одно упражнение в справочник")
        return

    workout_date = input_date("Дата тренировки (ДД.ММ.ГГГГ): ")
    workout_type = input("Тип тренировки (кардио/силовая): ")
    duration = input_int("Длительность (мин): ")

    exercises_done = []
    while True:
        show_exercises(exercises)
        exercise_id = input_int("ID упражнения (0 — закончить добавление): ")
        if exercise_id == 0:
            break
        if exercise_id not in exercises:
            print("Нет упражнения с таким id")
            continue
        sets = input_int("Подходов: ")
        reps = input_int("Повторений: ")
        weight = input_int("Рабочий вес: ")
        exercises_done.append(
            {
                "exercise_id": exercise_id,
                "sets": sets,
                "reps": reps,
                "weight": weight,
            }
        )

    try:
        create_workout(workouts, workout_date, workout_type, exercises_done, duration)
        save_workouts(WORKOUTS_FILE, workouts)
        print(trening_result(True, 0, exercises_done))
    except ValueError as e:
        print(f"Ошибка: {e}")
        print(trening_result(False, 0, exercises_done))


def cancel_workout_menu(workouts: list[dict]) -> None:
    """Пункт меню: отменить тренировку."""
    show_workouts(workouts)
    workout_id = input_int("ID тренировки для отмены: ")
    try:
        cancel_workout(workouts, workout_id)
        save_workouts(WORKOUTS_FILE, workouts)
        print("Тренировка отменена")
    except ValueError as e:
        print(f"Ошибка: {e}")


def show_stats_menu(workouts: list[dict]) -> None:
    """Пункт меню: показать статистику тренировок."""
    stats = get_workout_stats(workouts)
    print(f"Всего тренировок: {stats['total_workouts']}")
    print(f"Суммарная длительность: {stats['total_duration_min']} мин")
    for workout_type, count in stats["by_type"].items():
        print(f"  {workout_type}: {count}")


def create_result_menu(results: list[dict], workouts: list[dict]) -> None:
    """Пункт меню: сформировать результат за период времени."""
    period_start = input_date("Начало периода (ДД.ММ.ГГГГ): ")
    period_end = input_date("Конец периода (ДД.ММ.ГГГГ): ")
    try:
        result = create_result(results, workouts, period_start, period_end)
        save_results(RESULTS_FILE, results)
        print(
            f"Результат №{result['id']} создан, тренировок в периоде: "
            f"{len(result['workout_ids'])}"
        )
    except ValueError as e:
        print(f"Ошибка: {e}")


def show_result_stats_menu(results: list[dict], workouts: list[dict]) -> None:
    """Пункт меню: показать статистику по результату за период."""
    if not results:
        print("Результатов пока нет")
        return
    for result in results:
        print(f"{result['id']}. {result['period_start']} — " f"{result['period_end']}")
    result_id = input_int("ID результата: ")
    try:
        result = find_result_by_id(results, result_id)
        stats = get_result_stats(result, workouts)
        print(f"Тренировок за период: {stats['total_workouts']}")
        print(f"Суммарная длительность: {stats['total_duration_min']} мин")
        for workout_type, count in stats["by_type"].items():
            print(f"  {workout_type}: {count}")
    except ValueError as e:
        print(f"Ошибка: {e}")


MENU = """
=== Сервис учета тренировок ===
1. Показать упражнения
2. Добавить упражнение
3. Найти упражнение
4. Фильтр упражнений по группе мышц
5. Добавить тренировку
6. Отменить тренировку
7. Показать тренировки
8. Статистика по тренировкам
9. Сформировать результат за период
10. Статистика по результату за период
0. Выход
"""


def main() -> None:
    """Точка запуска приложения."""
    exercises = load_exercises(EXERCISES_FILE)
    workouts = load_workouts(WORKOUTS_FILE)
    results = load_results(RESULTS_FILE)

    actions = {
        "1": lambda: show_exercises(exercises),
        "2": lambda: add_exercise_menu(exercises),
        "3": lambda: find_exercise_menu(exercises),
        "4": lambda: filter_exercise_menu(exercises),
        "5": lambda: add_workout_menu(workouts, exercises),
        "6": lambda: cancel_workout_menu(workouts),
        "7": lambda: show_workouts(workouts),
        "8": lambda: show_stats_menu(workouts),
        "9": lambda: create_result_menu(results, workouts),
        "10": lambda: show_result_stats_menu(results, workouts),
    }

    while True:
        print(MENU)
        choice = input("Выберите действие: ")
        if choice == "0":
            print("До встречи!")
            break
        action = actions.get(choice)
        if action is None:
            print("Неизвестный пункт меню")
            continue
        action()


if __name__ == "__main__":
    main()
