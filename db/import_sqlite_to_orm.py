"""Перенос данных из базы ПР7 (SQLite, data/workout_app.sqlite) в модели Django.

Запуск из корня проекта (после `python manage.py migrate`):

    python -m db.import_sqlite_to_orm

Исходная база открывается только для чтения и не изменяется. Данные
записываются через ORM в базу, указанную в DATABASES (db.sqlite3), одной
транзакцией: при ошибке изменения откатываются. Первичные ключи сохраняются,
поэтому все связи остаются прежними. Скрипт можно запускать повторно:
записи с совпадающими идентификаторами обновляются, а не дублируются.

Порядок переноса повторяет зависимости сущностей: сначала независимые
(пользователи, упражнения), затем тренировки, строки упражнений, результаты.
"""

import os
import sys
from datetime import date
from pathlib import Path

import django
from django.db import transaction

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workout_app.settings")
django.setup()

# Модели импортируются только после django.setup().
from exercises.models import Exercise  # noqa: E402
from results.models import Result  # noqa: E402
from users.models import User  # noqa: E402
from workouts.models import Workout, WorkoutExercise  # noqa: E402

from db.inspect_source_db import (  # noqa: E402
    SOURCE_DB,
    find_integrity_problems,
    open_source,
)


def import_all(source_path: Path = SOURCE_DB) -> dict[str, int]:
    """Перенести все таблицы из исходной базы и вернуть число записей в ORM."""
    conn = open_source(source_path)
    try:
        problems = find_integrity_problems(conn)
        if problems:
            raise ValueError(
                "Исходная база нарушает ссылочную целостность:\n" + "\n".join(problems)
            )

        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        exercises = conn.execute("SELECT * FROM exercises ORDER BY id").fetchall()
        workouts = conn.execute("SELECT * FROM workouts ORDER BY id").fetchall()
        items = conn.execute("SELECT * FROM workout_exercises ORDER BY id").fetchall()
        results = conn.execute("SELECT * FROM results ORDER BY id").fetchall()
        links = conn.execute(
            "SELECT result_id, workout_id FROM result_workouts "
            "ORDER BY result_id, workout_id"
        ).fetchall()
    finally:
        conn.close()

    with transaction.atomic():
        for row in users:
            User.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "name": row["name"],
                    "registered_at": date.fromisoformat(row["registered_at"]),
                },
            )
        for row in exercises:
            Exercise.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"], "muscle_group": row["muscle_group"]},
            )
        for row in workouts:
            Workout.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "user_id": row["user_id"],
                    "workout_date": date.fromisoformat(row["workout_date"]),
                    "workout_type": row["workout_type"],
                    "duration_min": row["duration_min"],
                    "status": (
                        Workout.Status.CANCELLED
                        if row["is_cancelled"]
                        else Workout.Status.ACTIVE
                    ),
                },
            )
        for row in items:
            WorkoutExercise.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "workout_id": row["workout_id"],
                    "exercise_id": row["exercise_id"],
                    "sets": row["sets"],
                    "reps": row["reps"],
                    "weight": row["weight"],
                },
            )
        for row in results:
            Result.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "user_id": row["user_id"],
                    "period_start": date.fromisoformat(row["period_start"]),
                    "period_end": date.fromisoformat(row["period_end"]),
                },
            )
        for result in Result.objects.filter(pk__in={row["result_id"] for row in links}):
            result.workouts.set(
                [row["workout_id"] for row in links if row["result_id"] == result.pk]
            )

    return {
        "users": User.objects.count(),
        "exercises": Exercise.objects.count(),
        "workouts": Workout.objects.count(),
        "workout_exercises": WorkoutExercise.objects.count(),
        "results": Result.objects.count(),
        "result_workouts": Result.workouts.through.objects.count(),
    }


def main() -> None:
    counts = import_all()
    print("Перенос данных завершён. Записей в базе Django:")
    for name, number in counts.items():
        print(f"  {name}: {number}")


if __name__ == "__main__":
    main()
