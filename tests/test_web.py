"""Тесты веб-слоя Django: маршруты, страницы и коды ответов."""

from django.test import Client, override_settings


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
