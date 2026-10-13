"""Корневая конфигурация маршрутов проекта «Сервис учета тренировок».

Здесь подключаются маршруты приложений; конкретные адреса страниц
описаны в файлах urls.py самих приложений.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("exercises/", include("exercises.urls")),
    path("workouts/", include("workouts.urls")),
]

# Обработчик ошибки 404 читается только из корневого urls.py проекта.
handler404 = "homepage.views.page_not_found"
