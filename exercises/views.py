"""View-функции приложения exercises: список и страница упражнения."""

from django.shortcuts import render

from models.exercises import find_exercise_by_id, sort_exercises
from models.workouts import find_workouts_with_exercise
from storage import load_exercises, load_users, load_workouts

EXERCISES_FILE = "data/exercises.json"
USERS_FILE = "data/users.json"
WORKOUTS_FILE = "data/workouts.json"


def exercises(request):
    """Страница /exercises/: список упражнений из data/exercises.json."""
    exercises_list = sort_exercises(load_exercises(EXERCISES_FILE))

    context = {
        "exercises": exercises_list,
    }

    return render(
        request,
        "exercises/exercise_list.html",
        context,
    )


def exercise_detail(request, exercise_id):
    """Страница /exercises/<id>/: информация об упражнении.

    Если упражнение не найдено, шаблон показывает сообщение об этом,
    а ответ возвращается с кодом 404.
    """
    exercises_list = load_exercises(EXERCISES_FILE)
    exercise = find_exercise_by_id(exercises_list, exercise_id)

    used_count = 0
    if exercise is not None:
        users_list = load_users(USERS_FILE)
        workouts_list = load_workouts(WORKOUTS_FILE, users_list, exercises_list)
        used_count = len(find_workouts_with_exercise(workouts_list, exercise))

    context = {
        "exercise": exercise,
        "used_count": used_count,
    }

    return render(
        request,
        "exercises/exercise_detail.html",
        context,
        status=404 if exercise is None else 200,
    )
