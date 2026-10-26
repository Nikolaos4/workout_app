"""View-функции приложения workouts: список и страница тренировки."""

from django.shortcuts import render

from models.workouts import find_workout_by_id
from storage import load_exercises, load_users, load_workouts

EXERCISES_FILE = "data/exercises.json"
USERS_FILE = "data/users.json"
WORKOUTS_FILE = "data/workouts.json"


def load_all_workouts():
    """Загрузить тренировки вместе со связанными пользователями и упражнениями."""
    exercises_list = load_exercises(EXERCISES_FILE)
    users_list = load_users(USERS_FILE)
    return load_workouts(WORKOUTS_FILE, users_list, exercises_list)


def workouts(request):
    """Страница /workouts/: список тренировок из data/workouts.json."""
    context = {
        "workouts": load_all_workouts(),
    }

    return render(
        request,
        "workouts/workout_list.html",
        context,
    )


def workout_detail(request, workout_id):
    """Страница /workouts/<id>/: информация о тренировке.

    Если тренировка не найдена, шаблон показывает сообщение об этом,
    а ответ возвращается с кодом 404.
    """
    workout = find_workout_by_id(load_all_workouts(), workout_id)

    context = {
        "workout": workout,
    }

    return render(
        request,
        "workouts/workout_detail.html",
        context,
        status=404 if workout is None else 200,
    )
