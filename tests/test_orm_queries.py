"""Тесты страниц, получающих данные через Django ORM (ПР9).

Проверяются выборки, фильтрация, поиск, сортировка, связи, агрегаты и
постраничный вывод, а также обработка пустых и некорректных значений.
"""

import re
from datetime import date

import pytest
from django.test import Client

from exercises.models import Exercise
from users.models import User
from workouts.models import Workout
from workouts.views import PAGE_SIZE

pytestmark = pytest.mark.django_db


def get(url, params=None):
    return Client(HTTP_HOST="localhost").get(url, params or {})


def ids(response):
    """Идентификаторы тренировок на странице списка в порядке отображения."""
    return [workout.pk for workout in response.context["workouts"]]


# --- упражнения: чтение, один объект, связи, exclude --------------------------


def test_lists_and_details_use_orm(base_data):
    Exercise.objects.filter(pk=1).update(name="Тестовое упражнение")
    assert "Тестовое упражнение" in get("/exercises/").content.decode()
    assert "Тестовое упражнение" in get("/workouts/1/").content.decode()


def test_exercises_are_sorted_by_name(base_data):
    names = [e.name for e in get("/exercises/").context["exercises"]]
    assert names == sorted(names)


def test_exercise_detail_counts_workouts(base_data):
    html = get("/exercises/1/").content.decode()
    assert "Выполнялось в тренировках" in html
    assert 'bg-success">1<' in html


def test_exercise_detail_ignores_cancelled_workouts(demo_data):
    # Жим лёжа есть в тренировках 1, 2, 4 и в отменённой 5.
    assert get("/exercises/1/").context["used_count"] == 3


def test_exercise_used_twice_in_one_workout_is_counted_once(base_data):
    from workouts.models import WorkoutExercise

    WorkoutExercise.objects.create(
        workout=base_data.workout, exercise=base_data.bench, sets=1, reps=1, weight=1
    )
    assert get("/exercises/1/").context["used_count"] == 1


def test_exercise_detail_lists_other_exercises_of_same_group(base_data):
    Exercise.objects.create(name="Жим гантелей", muscle_group="Грудь")
    response = get("/exercises/1/")
    assert [e.name for e in response.context["same_group"]] == ["Жим гантелей"]
    assert "Жим гантелей" in response.content.decode()


def test_exercise_detail_without_neighbours_hides_block(base_data):
    html = get("/exercises/2/").content.decode()
    assert "Другие упражнения этой группы мышц" not in html


def test_missing_objects_return_404(base_data):
    assert get("/exercises/999/").status_code == 404
    assert get("/workouts/999/").status_code == 404


def test_workout_detail_shows_joined_data(base_data):
    html = get("/workouts/1/").content.decode()
    assert "Николай Аниканов" in html
    assert "07.09.2026" in html
    assert "тоннаж 1920 кг" in html


def test_workout_detail_uses_few_queries(base_data, django_assert_max_num_queries):
    # Тренировка вместе с пользователем + строки вместе с упражнениями.
    with django_assert_max_num_queries(2):
        get("/workouts/1/")


# --- поиск упражнений ------------------------------------------------------


def test_exercise_search_by_muscle_group(base_data):
    html = get("/exercises/search/", {"muscle_group": "Ноги"}).content.decode()
    assert "Присед" in html
    assert "Молотки" not in html


def test_exercise_search_by_name_fragment(base_data):
    response = get("/exercises/search/", {"muscle_group": "Грудь", "name": "лёжа"})
    assert [e.name for e in response.context["exercises"]] == ["Жим лёжа"]


def test_exercise_search_with_unknown_fragment(base_data):
    html = get(
        "/exercises/search/", {"muscle_group": "Ноги", "name": "Нет"}
    ).content.decode()
    assert "Подходящих упражнений не найдено." in html


def test_exercise_search_without_group_shows_form_only(base_data):
    response = get("/exercises/search/")
    assert response.status_code == 200
    assert list(response.context["muscle_groups"]) == ["Бицепс", "Грудь", "Ноги"]
    assert list(response.context["exercises"]) == []


def test_exercise_search_is_safe_from_sql_injection(base_data):
    response = get("/exercises/search/", {"muscle_group": "' OR '1'='1"})
    assert response.status_code == 200
    assert "Подходящих упражнений не найдено." in response.content.decode()


# --- список тренировок: фильтры ----------------------------------------------


def test_workouts_list_filter_active_only(demo_data):
    all_html = get("/workouts/").content.decode()
    active_html = get("/workouts/", {"active": "1"}).content.decode()
    assert "Всего тренировок: 5" in all_html
    assert "Всего тренировок: 4" in active_html
    assert 'href="/workouts/5/"' in all_html
    assert 'href="/workouts/5/"' not in active_html


def test_workouts_list_filter_by_period(demo_data):
    response = get("/workouts/", {"start": "2026-09-14", "end": "2026-09-15"})
    assert sorted(ids(response)) == [2, 4]


def test_workouts_list_open_period_has_one_border_only(demo_data):
    assert sorted(ids(get("/workouts/", {"start": "2026-09-20"}))) == [3, 5]
    assert sorted(ids(get("/workouts/", {"end": "2026-09-08"}))) == [1]


def test_workouts_list_invalid_date_shows_message(base_data):
    response = get("/workouts/", {"start": "вчера"})
    assert response.status_code == 200
    assert "Некорректная дата" in response.content.decode()
    assert ids(response) == []


def test_workouts_list_empty_result(base_data):
    html = get("/workouts/", {"start": "2030-01-01"}).content.decode()
    assert "Тренировок не найдено." in html


def test_workouts_list_filter_by_user(demo_data):
    assert sorted(ids(get("/workouts/", {"user": "2"}))) == [4, 5]


def test_workouts_list_filter_by_type(demo_data):
    assert ids(get("/workouts/", {"type": "кардио"})) == [3]


def test_workouts_list_unknown_type_and_user_are_ignored(demo_data):
    response = get("/workouts/", {"type": "йога", "user": "abc"})
    assert response.status_code == 200
    assert response.context["total"] == 5


def test_workouts_list_search_by_user_name(demo_data):
    assert sorted(ids(get("/workouts/", {"q": "Мария"}))) == [4, 5]


def test_workouts_list_search_by_type_field(demo_data):
    assert ids(get("/workouts/", {"q": "кардио"})) == [3]


def test_workouts_list_combined_filters(demo_data):
    response = get("/workouts/", {"user": "1", "active": "1", "type": "силовая"})
    assert sorted(ids(response)) == [1, 2]


# --- список тренировок: сортировка --------------------------------------------


def test_workouts_default_sort_is_newest_first(demo_data):
    assert ids(get("/workouts/")) == [5, 3, 4, 2, 1]


def test_workouts_sort_by_date_ascending(demo_data):
    assert ids(get("/workouts/", {"sort": "date_asc"})) == [1, 2, 4, 3, 5]


def test_workouts_sort_by_user_then_date(demo_data):
    # «Мария Петрова» раньше «Николай Аниканов»; внутри пользователя — новые первыми.
    assert ids(get("/workouts/", {"sort": "user"})) == [5, 4, 3, 2, 1]


def test_workouts_sort_by_duration(demo_data):
    assert ids(get("/workouts/", {"sort": "duration"})) == [1, 2, 5, 4, 3]


def test_workouts_sort_by_tonnage_uses_annotation(demo_data):
    # Тоннаж: 1 — 4880, 2 — 3530, 4 — 2640, 5 — 1350, 3 — 0.
    assert ids(get("/workouts/", {"sort": "tonnage"})) == [1, 2, 4, 5, 3]


def test_workouts_unknown_sort_falls_back_to_default(demo_data):
    default = ids(get("/workouts/"))
    assert ids(get("/workouts/", {"sort": "id; DROP TABLE x"})) == default
    assert ids(get("/workouts/", {"sort": "user__password"})) == default


def test_workouts_annotations_count_exercises_and_tonnage(demo_data):
    first = get("/workouts/").context["workouts"]
    by_id = {w.pk: w for w in first}
    assert by_id[1].exercises_count == 3
    assert by_id[1].tonnage == 4880
    assert by_id[3].tonnage == 0


def test_workout_without_exercises_stays_in_list(base_data):
    empty = Workout.objects.create(
        user=base_data.user, workout_date=date(2026, 9, 9), workout_type="кардио"
    )
    response = get("/workouts/")
    assert empty.pk in ids(response)
    row = next(w for w in response.context["workouts"] if w.pk == empty.pk)
    assert (row.exercises_count, row.tonnage) == (0, 0)


def test_workouts_list_has_no_n_plus_one(demo_data, django_assert_max_num_queries):
    # Число страниц + сама страница + список пользователей для фильтра.
    with django_assert_max_num_queries(3):
        get("/workouts/")


# --- постраничный вывод --------------------------------------------------------


@pytest.fixture
def many_workouts(base_data):
    """12 активных тренировок подряд: вместе с base_data всего 13."""
    for day in range(1, 13):
        Workout.objects.create(
            user=base_data.user,
            workout_date=date(2026, 10, day),
            workout_type="кардио",
            duration_min=day,
        )


def test_pagination_splits_list(many_workouts):
    response = get("/workouts/")
    assert len(response.context["workouts"]) == PAGE_SIZE
    assert response.context["page_obj"].paginator.num_pages == 3
    assert response.context["total"] == 13


def test_pagination_second_page_continues_list(many_workouts):
    first = ids(get("/workouts/"))
    second = ids(get("/workouts/", {"page": "2"}))
    assert not set(first) & set(second)
    assert len(second) == PAGE_SIZE


def test_pagination_invalid_page_values_do_not_crash(many_workouts):
    assert ids(get("/workouts/", {"page": "abc"})) == ids(get("/workouts/"))
    last = get("/workouts/", {"page": "999"})
    assert last.status_code == 200
    assert last.context["page_obj"].number == 3


def test_pagination_links_keep_filters_and_sort(many_workouts):
    html = get(
        "/workouts/", {"active": "1", "sort": "duration", "type": "кардио"}
    ).content.decode()
    links = re.findall(r'href="(\?[^"]*page=\d+[^"]*)"', html)
    assert links
    for link in links:
        assert "sort=duration" in link
        assert "active=1" in link
        assert "type=%D0%BA%D0%B0%D1%80%D0%B4%D0%B8%D0%BE" in link


def test_pagination_hidden_when_single_page(demo_data):
    assert "pagination" not in get("/workouts/").content.decode()


def test_pagination_shown_for_multiple_pages(many_workouts):
    assert 'class="pagination' in get("/workouts/").content.decode()


# --- статистика ------------------------------------------------------------------


def test_statistics_page(demo_data):
    html = get("/workouts/statistics/").content.decode()
    assert "Тренировок: 4" in html
    assert "Тоннаж по группам мышц" in html


def test_statistics_summary_values(demo_data):
    summary = get("/workouts/statistics/").context["summary"]
    assert summary["workouts_count"] == 4
    assert summary["avg_duration"] == 47.5
    assert summary["first_date"] == date(2026, 9, 7)
    assert summary["last_date"] == date(2026, 9, 21)


def test_statistics_exercise_popularity_ignores_cancelled(demo_data):
    items = {
        e.name: e.workouts_count
        for e in get("/workouts/statistics/").context["exercise_popularity"]
    }
    # Жим лёжа: тренировки 1, 2, 4; отменённая 5 не считается.
    assert items["Жим лёжа"] == 3


def test_statistics_keeps_exercises_without_workouts(base_data):
    Exercise.objects.create(name="Тяга", muscle_group="Спина")
    response = get("/workouts/statistics/")
    items = {e.name: e.workouts_count for e in response.context["exercise_popularity"]}
    assert items["Тяга"] == 0
    assert "Тяга" in response.content.decode()


def test_statistics_muscle_group_tonnage_ignores_cancelled(demo_data):
    rows = get("/workouts/statistics/").context["muscle_group_tonnage"]
    tonnage = {row["muscle_group"]: row["tonnage"] for row in rows}
    assert tonnage["Грудь"] == 1920 + 2720 + 1200
    assert tonnage["Ноги"] == 2000 + 0 + 1440
    assert tonnage["Бицепс"] == 960 + 810


def test_statistics_having_threshold(demo_data):
    low = get("/workouts/statistics/", {"min_workouts": "2"}).content.decode()
    high = get("/workouts/statistics/", {"min_workouts": "5"}).content.decode()
    assert "Николай Аниканов" in low
    assert "Мария Петрова" not in low
    assert "Нет пользователей с таким числом тренировок." in high


def test_statistics_active_users_totals(demo_data):
    users = {
        u.name: (u.workouts_count, u.total_minutes)
        for u in get("/workouts/statistics/").context["active_users"]
    }
    assert users["Николай Аниканов"] == (3, 60 + 55 + 30)
    assert users["Мария Петрова"] == (1, 45)


def test_statistics_user_with_only_cancelled_workouts_is_hidden(base_data):
    user = User.objects.create(name="Отменивший")
    Workout.objects.create(
        user=user,
        workout_date=date(2026, 9, 1),
        workout_type="кардио",
        is_cancelled=True,
    )
    html = get("/workouts/statistics/", {"min_workouts": "0"}).content.decode()
    assert "Отменивший" not in html


@pytest.mark.parametrize("value", ["abc", "-5", "", "99999999999999999999"])
def test_statistics_bad_threshold_does_not_crash(base_data, value):
    response = get("/workouts/statistics/", {"min_workouts": value})
    assert response.status_code == 200


def test_statistics_on_empty_database(db):
    html = get("/workouts/statistics/").content.decode()
    assert "Данные отсутствуют." in html


def test_navigation_contains_statistics_link(base_data):
    assert 'href="/workouts/statistics/"' in get("/").content.decode()
