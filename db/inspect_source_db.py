"""Осмотр исходной базы ПР7 перед переносом данных в Django ORM.

Запуск из корня проекта:  python -m db.inspect_source_db

Скрипт только читает базу data/workout_app.sqlite: выводит таблицы, столбцы
и количество записей, а затем проверяет ссылочную целостность (все внешние
ключи указывают на существующие записи).
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "workout_app.sqlite"

# Проверки внешних ключей: (описание, SQL, возвращающий «висячие» записи).
INTEGRITY_CHECKS = (
    (
        "workouts.user_id -> users.id",
        "SELECT w.id FROM workouts w LEFT JOIN users u ON u.id = w.user_id "
        "WHERE u.id IS NULL",
    ),
    (
        "workout_exercises.workout_id -> workouts.id",
        "SELECT we.id FROM workout_exercises we "
        "LEFT JOIN workouts w ON w.id = we.workout_id WHERE w.id IS NULL",
    ),
    (
        "workout_exercises.exercise_id -> exercises.id",
        "SELECT we.id FROM workout_exercises we "
        "LEFT JOIN exercises e ON e.id = we.exercise_id WHERE e.id IS NULL",
    ),
    (
        "results.user_id -> users.id",
        "SELECT r.id FROM results r LEFT JOIN users u ON u.id = r.user_id "
        "WHERE u.id IS NULL",
    ),
    (
        "result_workouts.result_id -> results.id",
        "SELECT rw.result_id FROM result_workouts rw "
        "LEFT JOIN results r ON r.id = rw.result_id WHERE r.id IS NULL",
    ),
    (
        "result_workouts.workout_id -> workouts.id",
        "SELECT rw.workout_id FROM result_workouts rw "
        "LEFT JOIN workouts w ON w.id = rw.workout_id WHERE w.id IS NULL",
    ),
)


def open_source(path: Path = SOURCE_DB) -> sqlite3.Connection:
    """Открыть исходную базу только для чтения (изменить её нельзя)."""
    if not path.exists():
        raise FileNotFoundError(f"Исходная база не найдена: {path}")
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def find_integrity_problems(conn: sqlite3.Connection) -> list[str]:
    """Вернуть описания нарушений ссылочной целостности (пустой список — ок)."""
    problems = []
    for title, sql in INTEGRITY_CHECKS:
        broken = [row[0] for row in conn.execute(sql)]
        if broken:
            problems.append(f"{title}: нет родительской записи для {broken}")
    return problems


def main() -> None:
    conn = open_source()
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        for (table_name,) in tables:
            print(f"\nТаблица: {table_name}")
            for column in conn.execute(f'PRAGMA table_info("{table_name}")'):
                print(
                    f"  {column['name']}: {column['type']}, "
                    f"NOT NULL={column['notnull']}, PK={column['pk']}"
                )
            count = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
            print(f"  Записей: {count}")

        problems = find_integrity_problems(conn)
        print("\nСсылочная целостность:", "нарушений нет" if not problems else "")
        for problem in problems:
            print(" -", problem)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
