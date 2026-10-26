"""Тесты веб-слоя Django: маршруты, страницы и коды ответов."""

from django.test import Client, override_settings
from django.urls import reverse


def get(url: str):
    """Выполнить GET-запрос к приложению без запуска сервера."""
    return Client(HTTP_HOST="localhost").get(url)


def test_index_page():
    response = get("/")
    assert response.status_code == 200
    assert "Сервис учета тренировок" in response.content.decode()


def test_pages_contain_navigation_and_bootstrap():
    html = get("/").content.decode()
    assert 'href="/exercises/"' in html
    assert 'href="/workouts/"' in html
    assert "bootstrap" in html


def test_exercises_list_page():
    response = get("/exercises/")
    assert response.status_code == 200
    assert "Жим лёжа" in response.content.decode()


def test_exercise_detail_page():
    response = get("/exercises/1/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Жим лёжа" in html
    assert "Выполнялось в тренировках" in html


def test_exercise_detail_not_found_returns_404():
    response = get("/exercises/999/")
    assert response.status_code == 404
    assert "Упражнение не найдено" in response.content.decode()


def test_workouts_list_page():
    response = get("/workouts/")
    assert response.status_code == 200
    assert 'href="/workouts/1/"' in response.content.decode()


def test_workout_detail_page_shows_related_objects():
    response = get("/workouts/1/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Николай Аниканов" in html
    assert "Жим лёжа" in html


def test_workout_detail_not_found_returns_404():
    response = get("/workouts/999/")
    assert response.status_code == 404
    assert "Тренировка не найдена" in response.content.decode()


@override_settings(DEBUG=False)
def test_unknown_url_uses_custom_404_page():
    response = get("/nonexistent/")
    assert response.status_code == 404
    assert "404 – страница не найдена" in response.content.decode()


@override_settings(DEBUG=False)
def test_non_integer_id_does_not_match_route():
    response = get("/exercises/abc/")
    assert response.status_code == 404
    assert "404 – страница не найдена" in response.content.decode()


def test_base_template_layout_and_static_files():
    html = get("/").content.decode()
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "/static/homepage/css/style.css" in html
    assert "/static/homepage/js/main.js" in html
    assert "/static/homepage/img/logo.png" in html
    assert 'id="current-year"' in html


def test_navigation_links_built_from_named_urls():
    html = get("/").content.decode()
    assert reverse("homepage:index") == "/"
    assert reverse("exercises:list") == "/exercises/"
    assert reverse("workouts:detail", args=[1]) == "/workouts/1/"
    assert f'href="{reverse("exercises:list")}"' in html


def test_exercises_list_uses_include_and_length_filter():
    html = get("/exercises/").content.decode()
    assert "Всего упражнений: 3" in html
    assert 'class="card exercise-card mb-3"' in html
    assert 'href="/exercises/1/"' in html


def test_workout_status_include_shows_active_state():
    html = get("/workouts/1/").content.decode()
    assert "активна" in html
    assert "workout-status-active" in html


def test_workout_date_formatted_by_filter():
    assert "07.09.2026" in get("/workouts/1/").content.decode()


def test_views_do_not_build_html_in_python():
    from homepage import views as homepage_views

    assert not hasattr(homepage_views, "page")
