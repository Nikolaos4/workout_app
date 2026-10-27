"""Перенос данных проекта из JSON-файлов каталога data/ в таблицы SQLite.

Запуск из корня проекта:  python -m db.import_json

Скрипт можно запускать повторно: перед вставкой таблицы очищаются, поэтому
база всегда точно соответствует JSON-файлам.
"""

import json
import sqlite3

from db.database import BASE_DIR, get_connection, init_db

DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
EXERCISES_FILE = DATA_DIR / "exercises.json"
WORKOUTS_FILE = DATA_DIR / "workouts.json"
RESULTS_FILE = DATA_DIR / "results.json"

# Порядок импорта: сначала таблицы, на которые ссылаются остальные.
TABLES_IN_IMPORT_ORDER = (
    "users",
    "exercises",
    "workouts",
    "workout_exercises",
    "results",
    "result_workouts",
)


def load_json(filename) -> list[dict]:
    """Прочитать список записей из JSON-файла."""
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn: sqlite3.Connection) -> None:
    """Удалить все записи; дочерние таблицы очищаются раньше родительских."""
    for table in reversed(TABLES_IN_IMPORT_ORDER):
        conn.execute(f"DELETE FROM {table}")


def import_users(conn: sqlite3.Connection) -> None:
    """Перенести пользователей."""
    users = load_json(USERS_FILE)
    conn.executemany(
        "INSERT INTO users (id, name, registered_at) VALUES (?, ?, ?)",
        [(u["id"], u["name"], u["registered_at"]) for u in users],
    )


def import_exercises(conn: sqlite3.Connection) -> None:
    """Перенести справочник упражнений."""
    exercises = load_json(EXERCISES_FILE)
    conn.executemany(
        "INSERT INTO exercises (id, name, muscle_group) VALUES (?, ?, ?)",
        [(e["id"], e["name"], e["muscle_group"]) for e in exercises],
    )


def import_workouts(conn: sqlite3.Connection) -> None:
    """Перенести тренировки и вложенные списки выполненных упражнений."""
    workouts = load_json(WORKOUTS_FILE)
    conn.executemany(
        """
        INSERT INTO workouts (
            id, user_id, workout_date, workout_type, duration_min, is_cancelled
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                w["id"],
                w["user_id"],
                w["date"],
                w["type"],
                w.get("duration_min", 0),
                int(w.get("is_cancelled", False)),
            )
            for w in workouts
        ],
    )
    conn.executemany(
        """
        INSERT INTO workout_exercises (
            workout_id, exercise_id, sets, reps, weight
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                w["id"],
                item["exercise_id"],
                item["sets"],
                item["reps"],
                item["weight"],
            )
            for w in workouts
            for item in w["exercises"]
        ],
    )


def import_results(conn: sqlite3.Connection) -> None:
    """Перенести результаты за период и состав тренировок в них."""
    results = load_json(RESULTS_FILE)
    conn.executemany(
        """
        INSERT INTO results (id, user_id, period_start, period_end)
        VALUES (?, ?, ?, ?)
        """,
        [(r["id"], r["user_id"], r["period_start"], r["period_end"]) for r in results],
    )
    conn.executemany(
        "INSERT INTO result_workouts (result_id, workout_id) VALUES (?, ?)",
        [(r["id"], workout_id) for r in results for workout_id in r["workout_ids"]],
    )


def import_all(conn: sqlite3.Connection) -> None:
    """Очистить таблицы и перенести все данные в порядке зависимостей."""
    clear_tables(conn)
    import_users(conn)
    import_exercises(conn)
    import_workouts(conn)
    import_results(conn)


def main() -> None:
    """Создать структуру (если нужно) и выполнить импорт в одной транзакции."""
    conn = get_connection()
    try:
        init_db(conn)
        import_all(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
