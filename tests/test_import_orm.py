"""Тесты переноса данных из базы ПР7 в модели Django (db/import_sqlite_to_orm.py)."""

import hashlib
import sqlite3

import pytest

import db.database as database
from db import import_json
from db.import_sqlite_to_orm import import_all
from exercises.models import Exercise
from results.models import Result
from users.models import User
from workouts.models import Workout, WorkoutExercise

pytestmark = pytest.mark.django_db

DEMO_DATA = database.BASE_DIR / "sql" / "demo_data.sql"


@pytest.fixture
def source_db(tmp_path, monkeypatch):
    """Исходная база ПР7 во временном каталоге: данные JSON + демо-данные."""
    path = tmp_path / "source.sqlite"
    monkeypatch.setattr(database, "DB_PATH", path)
    conn = database.get_connection()
    database.init_db(conn)
    import_json.import_all(conn)
    conn.executescript(DEMO_DATA.read_text(encoding="utf-8"))
    # Результат за период с двумя тренировками проверяет связь «многие ко многим».
    conn.execute(
        "INSERT INTO results (id, user_id, period_start, period_end) "
        "VALUES (1, 1, '2026-09-01', '2026-09-30')"
    )
    conn.executemany(
        "INSERT INTO result_workouts (result_id, workout_id) VALUES (1, ?)",
        [(1,), (2,)],
    )
    conn.commit()
    conn.close()
    return path


def source_counts(path):
    conn = sqlite3.connect(path)
    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "users",
            "exercises",
            "workouts",
            "workout_exercises",
            "results",
            "result_workouts",
        )
    }
    conn.close()
    return counts


def test_counts_match_source(source_db):
    assert import_all(source_db) == source_counts(source_db)


def test_primary_keys_are_preserved(source_db):
    import_all(source_db)
    assert sorted(Workout.objects.values_list("pk", flat=True)) == [1, 2, 3, 4, 5]
    assert sorted(User.objects.values_list("pk", flat=True)) == [1, 2]
    assert sorted(WorkoutExercise.objects.values_list("pk", flat=True)) == list(
        range(1, 10)
    )


def test_foreign_keys_and_values_are_preserved(source_db):
    import_all(source_db)
    workout = Workout.objects.select_related("user").get(pk=4)
    assert workout.user.name == "Мария Петрова"
    assert workout.workout_date.isoformat() == "2026-09-15"
    assert workout.duration_min == 45
    assert workout.is_cancelled is False
    assert Workout.objects.get(pk=5).is_cancelled is True
    row = WorkoutExercise.objects.select_related("exercise", "workout").get(pk=2)
    assert (row.workout_id, row.exercise.name, row.weight) == (1, "Присед", 100)
    assert Exercise.objects.get(pk=1).muscle_group == "Грудь"


def test_many_to_many_links_are_transferred(source_db):
    import_all(source_db)
    result = Result.objects.get(pk=1)
    assert sorted(result.workouts.values_list("pk", flat=True)) == [1, 2]
    assert result.period_end.isoformat() == "2026-09-30"


def test_import_can_be_repeated_without_duplicates(source_db):
    import_all(source_db)
    assert import_all(source_db) == source_counts(source_db)


def test_import_updates_changed_records(source_db):
    import_all(source_db)
    conn = sqlite3.connect(source_db)
    conn.execute("UPDATE exercises SET name = 'Жим лёжа' WHERE id = 1")
    conn.commit()
    conn.close()
    import_all(source_db)
    assert Exercise.objects.get(pk=1).name == "Жим лёжа"
    assert Exercise.objects.count() == 3


def test_source_database_is_not_modified(source_db):
    before = hashlib.sha256(source_db.read_bytes()).hexdigest()
    import_all(source_db)
    assert hashlib.sha256(source_db.read_bytes()).hexdigest() == before


def test_broken_foreign_key_stops_import_before_writing(source_db):
    conn = sqlite3.connect(source_db)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("UPDATE workouts SET user_id = 999 WHERE id = 2")
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="workouts.user_id"):
        import_all(source_db)
    assert User.objects.count() == 0


def test_missing_source_file_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_all(tmp_path / "nope.sqlite")
