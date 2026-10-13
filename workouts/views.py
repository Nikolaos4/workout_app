"""View-функции приложения workouts: список и страница тренировки."""

from django.http import HttpResponse
from django.utils.html import escape

from homepage.views import page
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
    items = ""
    for workout in load_all_workouts():
        status = "отменена" if workout.is_cancelled else "активна"
        badge = "bg-secondary" if workout.is_cancelled else "bg-success"
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/workouts/{workout.id}/">
                {workout.workout_date:%d.%m.%Y} – {workout.workout_type},
                {escape(workout.user.name)}
            </a>
            <span class="badge {badge}">{status}</span>
        </li>
        """
    if not items:
        items = '<li class="list-group-item">Тренировок пока нет</li>'
    content = f"""
    <h1>Тренировки</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Тренировки", content))


def workout_detail(request, workout_id):
    """Страница /workouts/<id>/: информация о тренировке.

    Если тренировка не найдена, возвращается страница с кодом 404.
    """
    workouts_list = load_all_workouts()

    workout = find_workout_by_id(workouts_list, workout_id)

    if workout is None:
        content = """
        <h1 class="text-danger">Тренировка не найдена</h1>
        <a href="/workouts/" class="btn btn-outline-secondary">
            ← к списку тренировок
        </a>
        """
        return HttpResponse(
            page("Тренировка не найдена", content),
            status=404,
        )

    status = "отменена" if workout.is_cancelled else "активна"
    badge = "bg-secondary" if workout.is_cancelled else "bg-success"
    exercises_items = ""
    for item in workout.exercises:
        exercises_items += f'<li class="list-group-item">{escape(str(item))}</li>'

    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Тренировка №{workout.id}</h5>
            <p class="card-text">
                Пользователь: {escape(workout.user.name)}
            </p>
            <p class="card-text">
                Дата: {workout.workout_date:%d.%m.%Y}
            </p>
            <p class="card-text">
                Тип: {workout.workout_type}, длительность:
                {workout.duration_min} мин
            </p>
            <p class="card-text">
                Статус: <span class="badge {badge}">{status}</span>
            </p>
            <p class="card-text">Выполненные упражнения:</p>
            <ul class="list-group mb-3">{exercises_items}</ul>
            <a href="/workouts/" class="btn btn-outline-secondary">
                ← к списку тренировок
            </a>
        </div>
    </div>
    """
    return HttpResponse(
        page(f"Тренировка №{workout.id}", content),
        status=200,
    )
