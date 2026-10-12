"""Точка запуска приложения «Сервис учета тренировок»."""

from models import User, WorkoutExercise
from models.exercises import (
    add_exercise,
    filter_exercises_by_muscle_group,
    find_exercise,
    find_exercise_by_id,
    show_exercises,
)
from models.results import (
    create_result,
    find_result_by_id,
    get_user_results,
    show_results,
)
from models.users import add_user, find_user, find_user_by_id, show_users
from models.workouts import (
    Workout,
    cancel_workout,
    create_workout,
    find_workout_by_id,
    get_user_workouts,
    get_workout_stats,
    show_workouts,
    trening_result,
)
from storage import (
    load_exercises,
    load_results,
    load_users,
    load_workouts,
    save_exercises,
    save_results,
    save_users,
    save_workouts,
)
from utils import input_date, input_int

EXERCISES_FILE = "data/exercises.json"
USERS_FILE = "data/users.json"
WORKOUTS_FILE = "data/workouts.json"
RESULTS_FILE = "data/results.json"
DEFAULT_USER_ID = 1

MENU = """
=== Сервис учета тренировок ===
Текущий пользователь: {user}
1. Показать упражнения
2. Добавить упражнение
3. Найти упражнение
4. Фильтр упражнений по группе мышц
5. Добавить тренировку
6. Отменить тренировку
7. Показать мои тренировки
8. Статистика по моим тренировкам
9. Сформировать результат за период
10. Статистика по результату за период
11. Показать пользователей
12. Добавить пользователя
13. Найти пользователя
14. Сменить пользователя
0. Выход
"""


def print_stats(stats: dict) -> None:
    """Вывести статистику тренировок."""
    print(f"Тренировок: {stats['total_workouts']}")
    print(f"Суммарная длительность: {stats['total_duration_min']} мин")
    for workout_type, count in stats["by_type"].items():
        print(f"  {workout_type}: {count}")


def add_exercise_menu(exercises: list) -> None:
    """Пункт меню: добавить упражнение в справочник."""
    name = input("Название упражнения: ")
    muscle_group = input("Рабочая группа мышц: ")
    try:
        exercise = add_exercise(exercises, name, muscle_group)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    save_exercises(EXERCISES_FILE, exercises)
    print(f"Упражнение добавлено: {exercise}")


def find_exercise_menu(exercises: list) -> None:
    """Пункт меню: найти упражнение по подстроке названия."""
    query = input("Подстрока для поиска: ")
    show_exercises(find_exercise(exercises, query))


def filter_exercise_menu(exercises: list) -> None:
    """Пункт меню: отфильтровать упражнения по группе мышц."""
    muscle_group = input("Группа мышц: ")
    show_exercises(filter_exercises_by_muscle_group(exercises, muscle_group))


def add_workout_menu(workouts: list, exercises: list, user: User) -> None:
    """Пункт меню: добавить тренировку текущему пользователю."""
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
        exercise = find_exercise_by_id(exercises, exercise_id)
        if exercise is None:
            print("Нет упражнения с таким id")
            continue
        sets = input_int("Подходов: ")
        reps = input_int("Повторений: ")
        weight = input_int("Рабочий вес: ")
        exercises_done.append(WorkoutExercise(exercise, sets, reps, weight))

    try:
        workout = create_workout(
            workouts, user, workout_date, workout_type, exercises_done, duration
        )
    except ValueError as error:
        print(f"Ошибка: {error}")
        print(trening_result(False, 0, exercises_done))
        return
    save_workouts(WORKOUTS_FILE, workouts)
    print(trening_result(True, 0, exercises_done))
    print(workout)


def cancel_workout_menu(workouts: list, user: User) -> None:
    """Пункт меню: отменить тренировку текущего пользователя."""
    user_workouts = get_user_workouts(workouts, user)
    if not user_workouts:
        print("Тренировок пока нет")
        return
    show_workouts(user_workouts)
    workout_id = input_int("ID тренировки для отмены: ")
    if find_workout_by_id(user_workouts, workout_id) is None:
        print("У вас нет тренировки с таким id")
        return
    if cancel_workout(workouts, workout_id):
        save_workouts(WORKOUTS_FILE, workouts)
        print("Тренировка отменена")
    else:
        print("Эта тренировка уже была отменена")


def show_stats_menu(workouts: list[Workout], user: User) -> None:
    """Пункт меню: статистика по тренировкам текущего пользователя."""
    print_stats(get_workout_stats(get_user_workouts(workouts, user)))


def create_result_menu(results: list, workouts: list, user: User) -> None:
    """Пункт меню: сформировать результат за период времени."""
    period_start = input_date("Начало периода (ДД.ММ.ГГГГ): ")
    period_end = input_date("Конец периода (ДД.ММ.ГГГГ): ")
    try:
        result = create_result(results, workouts, user, period_start, period_end)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    save_results(RESULTS_FILE, results)
    print(result)


def show_result_stats_menu(results: list, user: User) -> None:
    """Пункт меню: статистика по выбранному результату пользователя."""
    user_results = get_user_results(results, user)
    if not user_results:
        print("Результатов пока нет")
        return
    show_results(user_results)
    result_id = input_int("ID результата: ")
    try:
        result = find_result_by_id(user_results, result_id)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    print_stats(result.get_stats())


def add_user_menu(users: list) -> None:
    """Пункт меню: добавить пользователя."""
    name = input("Имя пользователя: ")
    try:
        add_user(users, name)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    save_users(USERS_FILE, users)
    print(f"Пользователь добавлен: {users[-1]}")


def find_user_menu(users: list) -> None:
    """Пункт меню: найти пользователя по имени."""
    query = input("Часть имени: ")
    show_users(find_user(users, query))


def choose_user_menu(users: list, current_user: User) -> User:
    """Пункт меню: выбрать текущего пользователя по id."""
    show_users(users)
    user = find_user_by_id(users, input_int("ID пользователя: "))
    if user is None:
        print("Нет пользователя с таким id, текущий не изменён")
        return current_user
    print(f"Текущий пользователь: {user.name}")
    return user


def select_start_user(users: list) -> User:
    """Выбрать пользователя при запуске; при отсутствии создать первого."""
    while not users:
        print("Пользователей пока нет, создайте первого.")
        add_user_menu(users)
    return find_user_by_id(users, DEFAULT_USER_ID) or users[0]


def main() -> None:
    """Точка запуска приложения: загрузка данных и главное меню."""
    exercises = load_exercises(EXERCISES_FILE)
    users = load_users(USERS_FILE)
    workouts = load_workouts(WORKOUTS_FILE, users, exercises)
    results = load_results(RESULTS_FILE, users, workouts)
    current_user = select_start_user(users)

    actions = {
        "1": lambda: show_exercises(exercises),
        "2": lambda: add_exercise_menu(exercises),
        "3": lambda: find_exercise_menu(exercises),
        "4": lambda: filter_exercise_menu(exercises),
        "5": lambda: add_workout_menu(workouts, exercises, current_user),
        "6": lambda: cancel_workout_menu(workouts, current_user),
        "7": lambda: show_workouts(get_user_workouts(workouts, current_user)),
        "8": lambda: show_stats_menu(workouts, current_user),
        "9": lambda: create_result_menu(results, workouts, current_user),
        "10": lambda: show_result_stats_menu(results, current_user),
        "11": lambda: show_users(users),
        "12": lambda: add_user_menu(users),
        "13": lambda: find_user_menu(users),
    }

    while True:
        print(MENU.format(user=current_user.name))
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            print("До встречи!")
            break
        if choice == "14":
            current_user = choose_user_menu(users, current_user)
            continue
        action = actions.get(choice)
        if action is None:
            print("Неизвестный пункт меню")
            continue
        action()


if __name__ == "__main__":
    main()
