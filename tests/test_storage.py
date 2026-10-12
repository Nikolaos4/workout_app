"""Тесты загрузки и сохранения объектов в JSON."""

import json
from datetime import date, timedelta

from models import Exercise, User, WorkoutExercise
from models.results import create_result
from models.workouts import cancel_workout, create_workout
from storage import (
    load_exercises,
    load_results,
    load_users,
    load_workouts,
    save_exercises,
    save_results,
    save_users,
    save_workouts,
)


def make_objects():
    user = User(1, "Иван Петров", date(2026, 9, 1))
    exercise = Exercise(1, "Жим лёжа", "Грудь")
    items = [WorkoutExercise(exercise, 3, 8, 80)]
    workouts = []
    day = date.today() - timedelta(days=2)
    create_workout(workouts, user, day, "силовая", items, 60)
    create_workout(workouts, user, day, "кардио", items, 30)
    cancel_workout(workouts, 2)
    return user, exercise, workouts


def test_roundtrip_restores_objects_and_links(tmp_path):
    user, exercise, workouts = make_objects()
    results = []
    create_result(
        results, workouts, user, date.today() - timedelta(days=5), date.today()
    )
    paths = {
        name: str(tmp_path / f"{name}.json")
        for name in ("exercises", "users", "workouts", "results")
    }

    save_exercises(paths["exercises"], [exercise])
    save_users(paths["users"], [user])
    save_workouts(paths["workouts"], workouts)
    save_results(paths["results"], results)

    loaded_exercises = load_exercises(paths["exercises"])
    loaded_users = load_users(paths["users"])
    loaded_workouts = load_workouts(paths["workouts"], loaded_users, loaded_exercises)
    loaded_results = load_results(paths["results"], loaded_users, loaded_workouts)

    assert loaded_users[0].registered_at == date(2026, 9, 1)
    assert loaded_workouts[0].user is loaded_users[0]
    assert loaded_workouts[0].exercises[0].exercise is loaded_exercises[0]
    assert loaded_workouts[0].workout_type == "силовая"
    assert loaded_workouts[1].is_cancelled
    assert loaded_results[0].user is loaded_users[0]
    assert loaded_results[0].workouts[0] is loaded_workouts[0]


def test_json_contains_only_ids_of_linked_objects(tmp_path):
    _, _, workouts = make_objects()
    path = tmp_path / "workouts.json"
    save_workouts(str(path), workouts)
    record = json.loads(path.read_text(encoding="utf-8"))[0]
    assert record["user_id"] == 1
    assert record["exercises"][0]["exercise_id"] == 1
    assert "user" not in record


def test_missing_file_gives_empty_collection(tmp_path):
    assert load_exercises(str(tmp_path / "none.json")) == []
    assert load_users(str(tmp_path / "none.json")) == []


def test_broken_json_gives_empty_collection_with_warning(tmp_path, capsys):
    path = tmp_path / "broken.json"
    path.write_text("{ не json", encoding="utf-8")
    assert load_exercises(str(path)) == []
    assert "повреждён" in capsys.readouterr().out


def test_workout_with_missing_user_is_skipped_with_warning(tmp_path, capsys):
    path = tmp_path / "workouts.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "user_id": 99,
                    "date": "2026-09-07",
                    "type": "силовая",
                    "duration_min": 60,
                    "exercises": [],
                    "is_cancelled": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    assert load_workouts(str(path), [], []) == []
    assert "пользователь 99 не найден" in capsys.readouterr().out


def test_workout_with_unknown_type_is_skipped(tmp_path, capsys):
    user = User(1, "Иван", date(2026, 9, 1))
    path = tmp_path / "workouts.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "user_id": 1,
                    "date": "2026-09-07",
                    "type": "йога",
                    "exercises": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    assert load_workouts(str(path), [user], []) == []
    assert "Неизвестный тип" in capsys.readouterr().out
