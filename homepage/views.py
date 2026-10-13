"""View-функции приложения homepage: каркас страниц, главная и страница 404."""

from django.http import HttpResponse
from django.utils.html import escape


def page(title, content):
    """Собрать HTML-страницу: кодировка, заголовок вкладки, Bootstrap, меню.

    title — заголовок вкладки (обычный текст), content — готовая HTML-разметка
    содержимого страницы. Остальные приложения импортируют эту функцию.
    """
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="{bootstrap}">
</head>
<body>
    <nav class="nav">
        <a class="nav-link" href="/">Главная</a>
        <a class="nav-link" href="/exercises/">Упражнения</a>
        <a class="nav-link" href="/workouts/">Тренировки</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


def index(request):
    """Главная страница: описание приложения и навигация."""
    content = """
    <h1 class="display-4">Сервис учета тренировок</h1>
    <p class="lead">Записывайте тренировки и следите за прогрессом.</p>
    <p>Основные разделы:</p>
    <a href="/exercises/" class="btn btn-primary me-2">Упражнения</a>
    <a href="/workouts/" class="btn btn-secondary">Тренировки</a>
    """
    return HttpResponse(page("Сервис учета тренировок", content))


def page_not_found(request, exception):
    """Обработчик ошибки 404: страница проекта с кодом статуса 404."""
    content = """
    <h1 class="text-danger">404 – страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a href="/" class="btn btn-primary">На главную</a>
    """
    return HttpResponse(
        page("404 – страница не найдена", content),
        status=404,
    )
