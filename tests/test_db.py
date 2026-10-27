"""Тесты слоя SQLite (ПР7): схема, импорт из JSON, SQL-запросы в представлениях."""

import json
import sqlite3

import pytest
from django.test import Client

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


def get(url):
    return Client(HTTP_HOST="localhost").get(url)


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


# --- страницы, получающие данные из SQLite ------------------------------


def test_lists_and_details_use_sqlite(imported_db):
    conn = get_connection()
    conn.execute("UPDATE exercises SET name = 'Тестовое упражнение' WHERE id = 1")
    conn.commit()
    conn.close()
    assert "Тестовое упражнение" in get("/exercises/").content.decode()
    assert "Тестовое упражнение" in get("/workouts/1/").content.decode()


def test_exercise_detail_counts_workouts_with_sql(imported_db):
    html = get("/exercises/1/").content.decode()
    assert "Выполнялось в тренировках" in html
    assert 'bg-success">1<' in html


def test_missing_objects_return_404(imported_db):
    assert get("/exercises/999/").status_code == 404
    assert get("/workouts/999/").status_code == 404


def test_workout_detail_shows_joined_data(imported_db):
    html = get("/workouts/1/").content.decode()
    assert "Николай Аниканов" in html
    assert "07.09.2026" in html
    assert "тоннаж 1920 кг" in html


def test_workouts_list_filter_active_only(demo_db):
    all_html = get("/workouts/").content.decode()
    active_html = get("/workouts/?active=1").content.decode()
    assert "Всего тренировок: 5" in all_html
    assert "Всего тренировок: 4" in active_html
    assert 'href="/workouts/5/"' in all_html
    assert 'href="/workouts/5/"' not in active_html


def test_workouts_list_filter_by_period(demo_db):
    html = get("/workouts/?start=2026-09-14&end=2026-09-15").content.decode()
    assert "Всего тренировок: 2" in html
    assert 'href="/workouts/2/"' in html
    assert 'href="/workouts/4/"' in html


def test_workouts_list_invalid_date_shows_message(imported_db):
    html = get("/workouts/?start=вчера").content.decode()
    assert "Некорректная дата" in html


def test_workouts_list_empty_result(imported_db):
    html = get("/workouts/?start=2030-01-01").content.decode()
    assert "Тренировок не найдено." in html


def test_exercise_search_by_muscle_group(imported_db):
    html = get("/exercises/search/?muscle_group=Ноги").content.decode()
    assert "Присед" in html
    assert "Молотки" not in html


def test_exercise_search_with_name_fragment(imported_db):
    html = get("/exercises/search/?muscle_group=Ноги&name=Нет").content.decode()
    assert "Подходящих упражнений не найдено." in html


def test_exercise_search_is_safe_from_sql_injection(imported_db):
    payload = "' OR '1'='1"
    response = get(f"/exercises/search/?muscle_group={payload}")
    assert response.status_code == 200
    assert "Подходящих упражнений не найдено." in response.content.decode()


def test_statistics_page(demo_db):
    html = get("/workouts/statistics/").content.decode()
    assert "Тренировок: 4" in html
    assert "Тоннаж по группам мышц" in html


def test_statistics_counts_only_active_workouts(demo_db):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM workouts WHERE is_cancelled = 0"
    ).fetchone()
    conn.close()
    assert row[0] == 4
    assert "Тренировок: 4" in get("/workouts/statistics/").content.decode()


def test_statistics_having_threshold(demo_db):
    low = get("/workouts/statistics/?min_workouts=2").content.decode()
    high = get("/workouts/statistics/?min_workouts=5").content.decode()
    assert "Николай Аниканов" in low
    assert "Мария Петрова" not in low
    assert "Нет пользователей с таким числом тренировок." in high


def test_statistics_bad_threshold_falls_back_to_default(imported_db):
    response = get("/workouts/statistics/?min_workouts=abc")
    assert response.status_code == 200


def test_statistics_on_empty_database(db_path):
    html = get("/workouts/statistics/").content.decode()
    assert "Данные отсутствуют." in html


def test_navigation_contains_statistics_link(imported_db):
    html = get("/").content.decode()
    assert 'href="/workouts/statistics/"' in html
