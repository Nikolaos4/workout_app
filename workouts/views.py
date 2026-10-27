"""View-функции приложения workouts: данные берутся из SQLite (ПР7)."""

import sqlite3
from contextlib import closing
from datetime import date

from django.shortcuts import render

from db.database import get_connection

# Границы периода по умолчанию: подходят любые даты формата YYYY-MM-DD.
MIN_DATE = "0000-01-01"
MAX_DATE = "9999-12-31"


def _parse_date(value):
    """Вернуть дату в виде строки YYYY-MM-DD или None, если формат неверный."""
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def _with_date(row):
    """Превратить строку результата в словарь с датой типа date.

    В SQLite дата хранится строкой, а фильтр шаблона date:"d.m.Y" работает
    только с объектами date.
    """
    workout = dict(row)
    workout["workout_date"] = date.fromisoformat(workout["workout_date"])
    return workout


def workouts(request):
    """Страница /workouts/: список тренировок из SQLite с фильтрами.

    GET-параметры: active=1 (только активные), start и end (период дат).
    Значения передаются в запрос именованными параметрами, а не в строку SQL.
    """
    only_active = request.GET.get("active") == "1"
    start_raw = request.GET.get("start", "")
    end_raw = request.GET.get("end", "")
    start = _parse_date(start_raw) if start_raw else MIN_DATE
    end = _parse_date(end_raw) if end_raw else MAX_DATE
    invalid_dates = start is None or end is None

    workouts_list = []
    if not invalid_dates:
        with closing(get_connection()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    workouts.id,
                    workouts.workout_date,
                    workouts.workout_type,
                    workouts.duration_min,
                    workouts.is_cancelled,
                    users.name AS user_name,
                    COUNT(workout_exercises.id) AS exercises_count,
                    COALESCE(
                        SUM(workout_exercises.sets
                            * workout_exercises.reps
                            * workout_exercises.weight),
                        0
                    ) AS tonnage
                FROM workouts
                JOIN users
                    ON workouts.user_id = users.id
                LEFT JOIN workout_exercises
                    ON workout_exercises.workout_id = workouts.id
                WHERE (:only_active = 0 OR workouts.is_cancelled = 0)
                  AND workouts.workout_date BETWEEN :start AND :end
                GROUP BY workouts.id, users.name
                ORDER BY workouts.workout_date DESC, workouts.id DESC;
                """,
                {"only_active": int(only_active), "start": start, "end": end},
            ).fetchall()
        workouts_list = [_with_date(row) for row in rows]

    context = {
        "workouts": workouts_list,
        "only_active": only_active,
        "start": start_raw,
        "end": end_raw,
        "invalid_dates": invalid_dates,
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
    items = []
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT
                workouts.id,
                workouts.workout_date,
                workouts.workout_type,
                workouts.duration_min,
                workouts.is_cancelled,
                users.name AS user_name
            FROM workouts
            JOIN users
                ON workouts.user_id = users.id
            WHERE workouts.id = ?;
            """,
            [workout_id],
        ).fetchone()

        if row is not None:
            items = conn.execute(
                """
                SELECT
                    exercises.name AS exercise_name,
                    exercises.muscle_group,
                    workout_exercises.sets,
                    workout_exercises.reps,
                    workout_exercises.weight,
                    workout_exercises.sets
                        * workout_exercises.reps
                        * workout_exercises.weight AS tonnage
                FROM workout_exercises
                JOIN exercises
                    ON workout_exercises.exercise_id = exercises.id
                WHERE workout_exercises.workout_id = ?
                ORDER BY workout_exercises.id;
                """,
                [workout_id],
            ).fetchall()

    workout = _with_date(row) if row is not None else None

    context = {
        "workout": workout,
        "items": items,
    }

    return render(
        request,
        "workouts/workout_detail.html",
        context,
        status=404 if workout is None else 200,
    )


def statistics(request):
    """Страница /workouts/statistics/: статистика по активным тренировкам.

    GET-параметр min_workouts задаёт порог для отбора пользователей (HAVING).
    """
    try:
        min_workouts = max(int(request.GET.get("min_workouts", 1)), 0)
    except ValueError:
        min_workouts = 1

    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        summary = conn.execute("""
            SELECT
                COUNT(*) AS workouts_count,
                AVG(duration_min) AS avg_duration,
                MIN(workout_date) AS first_date,
                MAX(workout_date) AS last_date
            FROM workouts
            WHERE is_cancelled = 0;
        """).fetchone()

        exercise_popularity = conn.execute("""
            SELECT
                exercises.name AS exercise_name,
                exercises.muscle_group,
                COUNT(DISTINCT workouts.id) AS workouts_count
            FROM exercises
            LEFT JOIN workout_exercises
                ON workout_exercises.exercise_id = exercises.id
            LEFT JOIN workouts
                ON workouts.id = workout_exercises.workout_id
               AND workouts.is_cancelled = 0
            GROUP BY exercises.id, exercises.name, exercises.muscle_group
            ORDER BY workouts_count DESC, exercises.name;
        """).fetchall()

        muscle_group_tonnage = conn.execute("""
            SELECT
                exercises.muscle_group,
                SUM(workout_exercises.sets
                    * workout_exercises.reps
                    * workout_exercises.weight) AS tonnage
            FROM workout_exercises
            JOIN exercises
                ON exercises.id = workout_exercises.exercise_id
            JOIN workouts
                ON workouts.id = workout_exercises.workout_id
            WHERE workouts.is_cancelled = 0
            GROUP BY exercises.muscle_group
            ORDER BY tonnage DESC;
        """).fetchall()

        active_users = conn.execute(
            """
            SELECT
                users.name AS user_name,
                COUNT(workouts.id) AS workouts_count,
                SUM(workouts.duration_min) AS total_minutes
            FROM users
            JOIN workouts
                ON workouts.user_id = users.id
            WHERE workouts.is_cancelled = 0
            GROUP BY users.id, users.name
            HAVING COUNT(workouts.id) >= ?
            ORDER BY workouts_count DESC, users.name;
            """,
            [min_workouts],
        ).fetchall()

    context = {
        "summary": summary,
        "exercise_popularity": exercise_popularity,
        "muscle_group_tonnage": muscle_group_tonnage,
        "active_users": active_users,
        "min_workouts": min_workouts,
    }

    return render(
        request,
        "workouts/statistics.html",
        context,
    )
