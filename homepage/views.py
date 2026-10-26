"""View-функции приложения homepage: главная страница и страница 404."""

from django.shortcuts import render


def index(request):
    """Главная страница: описание приложения и навигация."""
    return render(request, "homepage/index.html")


def page_not_found(request, exception):
    """Обработчик ошибки 404: страница проекта с кодом статуса 404."""
    return render(request, "homepage/404.html", status=404)
