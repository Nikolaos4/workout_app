"""View-функции приложения exercises: данные берутся из SQLite (ПР7)."""

import sqlite3
from contextlib import closing

from django.shortcuts import render

from db.database import get_connection


def exercises(request):
    """Страница /exercises/: список упражнений из таблицы exercises."""
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        exercises_list = conn.execute("""
            SELECT
                id,
                name,
                muscle_group
            FROM exercises
            ORDER BY name;
        """).fetchall()

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
    used_count = 0
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        exercise = conn.execute(
            """
            SELECT
                id,
                name,
                muscle_group
            FROM exercises
            WHERE id = ?;
            """,
            [exercise_id],
        ).fetchone()

        if exercise is not None:
            used_count = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT workouts.id) AS used_count
                FROM workout_exercises
                JOIN workouts
                    ON workouts.id = workout_exercises.workout_id
                WHERE workout_exercises.exercise_id = ?
                  AND workouts.is_cancelled = 0;
                """,
                [exercise_id],
            ).fetchone()["used_count"]

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


def exercise_search(request):
    """Страница /exercises/search/: поиск по группе мышц и названию.

    Значения приходят из GET-параметров и передаются в запрос только через
    заполнители ?, поэтому не могут изменить текст SQL.
    """
    muscle_group = request.GET.get("muscle_group", "")
    name = request.GET.get("name", "").strip()
    found = []

    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        muscle_groups = conn.execute("""
            SELECT DISTINCT
                muscle_group
            FROM exercises
            ORDER BY muscle_group;
        """).fetchall()

        if muscle_group:
            found = conn.execute(
                """
                SELECT
                    id,
                    name,
                    muscle_group
                FROM exercises
                WHERE muscle_group = ?
                  AND name LIKE '%' || ? || '%'
                ORDER BY name;
                """,
                [muscle_group, name],
            ).fetchall()

    context = {
        "muscle_groups": muscle_groups,
        "muscle_group": muscle_group,
        "name": name,
        "exercises": found,
    }

    return render(
        request,
        "exercises/exercise_search.html",
        context,
    )
