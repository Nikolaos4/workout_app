from django.conf import settings

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


admin.site.site_header = "Управление сервисом тренировок"
admin.site.site_title = "Тренировки"
admin.site.index_title = "Администрирование"

if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
