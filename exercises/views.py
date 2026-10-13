"""View-функции приложения exercises: список и страница упражнения."""

from django.http import HttpResponse
from django.utils.html import escape

from homepage.views import page
from models.exercises import find_exercise_by_id, sort_exercises
from models.workouts import find_workouts_with_exercise
from storage import load_exercises, load_users, load_workouts

EXERCISES_FILE = "data/exercises.json"
USERS_FILE = "data/users.json"
WORKOUTS_FILE = "data/workouts.json"


def exercises(request):
    """Страница /exercises/: список упражнений из data/exercises.json."""
    items = ""
    for exercise in sort_exercises(load_exercises(EXERCISES_FILE)):
        items += f"""
        <li class="list-group-item">
            <a href="/exercises/{exercise.id}/">{escape(exercise.name)}</a>
            – {escape(exercise.muscle_group)}
        </li>
        """
    if not items:
        items = '<li class="list-group-item">Упражнений пока нет</li>'
    content = f"""
    <h1>Упражнения</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Упражнения", content))


def exercise_detail(request, exercise_id):
    """Страница /exercises/<id>/: информация об упражнении.

    Если упражнение не найдено, возвращается страница с кодом 404.
    """
    exercises_list = load_exercises(EXERCISES_FILE)

    exercise = find_exercise_by_id(exercises_list, exercise_id)

    if exercise is None:
        content = """
        <h1 class="text-danger">Упражнение не найдено</h1>
        <a href="/exercises/" class="btn btn-outline-secondary">
            ← к списку упражнений
        </a>
        """
        return HttpResponse(
            page("Упражнение не найдено", content),
            status=404,
        )

    users_list = load_users(USERS_FILE)
    workouts_list = load_workouts(WORKOUTS_FILE, users_list, exercises_list)
    used_in = find_workouts_with_exercise(workouts_list, exercise)
    badge = "bg-success" if used_in else "bg-secondary"

    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">{escape(exercise.name)}</h5>
            <p class="card-text">
                <strong>ID:</strong> {exercise.id}
            </p>
            <p class="card-text">
                <strong>Группа мышц:</strong> {escape(exercise.muscle_group)}
            </p>
            <p class="card-text">
                Выполнялось в тренировках:
                <span class="badge {badge}">{len(used_in)}</span>
            </p>
            <a href="/exercises/" class="btn btn-outline-secondary">
                ← к списку упражнений
            </a>
        </div>
    </div>
    """
    return HttpResponse(
        page(exercise.name, content),
        status=200,
    )
