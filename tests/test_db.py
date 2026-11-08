"""Тесты слоя SQLite (ПР7): схема и импорт из JSON.

Страницы сайта с ПР9 работают через Django ORM, их проверяют
test_web.py и test_orm_queries.py."""

import json
import sqlite3

import pytest

import db.database as database
from db.database import get_connection, init_db
from db.import_json import (
    EXERCISES_FILE,
    RESULTS_FILE,
    USERS_FILE,
    WORKOUTS_FILE,
    import_all,
)

DEMO_DATA = database.BASE_DIR / "sql" / "demo_data.sql"


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Пустая база во временном каталоге, подставленная вместо рабочей."""
    path = tmp_path / "test.sqlite"
    monkeypatch.setattr(database, "DB_PATH", path)
    conn = get_connection()
    init_db(conn)
    conn.close()
    return path


@pytest.fixture
def imported_db(db_path):
    """База с данными, импортированными из JSON-файлов проекта."""
    conn = get_connection()
    import_all(conn)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def demo_db(imported_db):
    """База с импортом из JSON и демонстрационными данными поверх него."""
    conn = get_connection()
    conn.executescript(DEMO_DATA.read_text(encoding="utf-8"))
    conn.close()
    return imported_db


# --- структура базы -----------------------------------------------------


def test_schema_creates_all_tables(db_path):
    conn = get_connection()
    names = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    assert {
        "users",
        "exercises",
        "workouts",
        "workout_exercises",
        "results",
        "result_workouts",
    } <= names


def test_schema_can_be_applied_twice(db_path):
    conn = get_connection()
    init_db(conn)
    conn.close()


def test_foreign_keys_are_enforced(imported_db):
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO workouts (id, user_id, workout_date, workout_type) "
            "VALUES (99, 12345, '2026-09-01', 'силовая')"
        )
    conn.close()


def test_check_constraint_rejects_unknown_workout_type(imported_db):
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO workouts (id, user_id, workout_date, workout_type) "
            "VALUES (99, 1, '2026-09-01', 'йога')"
        )
    conn.close()


# --- импорт из JSON -----------------------------------------------------


def test_import_matches_json_files(imported_db):
    conn = get_connection()
    workouts = read_json(WORKOUTS_FILE)
    assert count(conn, "users") == len(read_json(USERS_FILE))
    assert count(conn, "exercises") == len(read_json(EXERCISES_FILE))
    assert count(conn, "workouts") == len(workouts)
    assert count(conn, "workout_exercises") == sum(
        len(w["exercises"]) for w in workouts
    )
    assert count(conn, "results") == len(read_json(RESULTS_FILE))
    conn.close()


def test_import_can_be_repeated_without_duplicates(imported_db):
    conn = get_connection()
    import_all(conn)
    conn.commit()
    assert count(conn, "workouts") == len(read_json(WORKOUTS_FILE))
    conn.close()


def test_import_converts_cancelled_flag_to_integer(imported_db):
    conn = get_connection()
    value = conn.execute("SELECT is_cancelled FROM workouts WHERE id = 1").fetchone()[0]
    conn.close()
    assert value == 0


def test_demo_data_is_added_on_top_of_json(demo_db):
    conn = get_connection()
    assert count(conn, "users") == 2
    assert count(conn, "workouts") == 5
    assert count(conn, "workout_exercises") == 9
    conn.close()
