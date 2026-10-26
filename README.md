# Сервис учета тренировок

## Назначение

Приложение для учета тренировок: пользователь записывает тренировки,
отслеживает прогресс, анализирует нагрузку и видит динамику результатов.
Консольная версия приложения (ПР1–ПР3) дополнена веб-интерфейсом на Django
(ПР5), страницы которого с ПР6 строятся на шаблонах Django.

Приложение позволяет:

* просматривать упражнения в браузере;
* просматривать информацию об отдельном упражнении и о том, в скольких
  тренировках оно выполнялось;
* просматривать список тренировок в браузере;
* просматривать информацию об отдельной тренировке, её пользователе и
  выполненных упражнениях;
* в консольной версии: добавлять упражнения, искать и фильтровать их,
  создавать и отменять тренировки, формировать результат за период,
  смотреть статистику, работать с пользователями;
* хранить данные между запусками приложения в JSON-файлах.

## Целевая аудитория

Люди, которые стремятся к здоровому образу жизни и хотят увеличить свою
спортивную активность.

## Используемые технологии

* Python 3;
* Django 5.2 — веб-фреймворк;
* Django Template Language (DTL) — шаблоны страниц;
* HTML5 — разметка веб-страниц;
* CSS3 и Bootstrap 5.3 — оформление страниц (Bootstrap подключён через CDN);
* JavaScript — небольшое клиентское поведение (текущий год в подвале);
* pytest — автоматизированные тесты;
* flake8 — проверка качества кода;
* black — форматирование кода.

## Предметная область

Основные объекты предметной области:

* упражнение — запись справочника (название, группа мышц);
* пользователь — тот, кто записывает тренировки;
* тренировка — выполненная пользователем тренировка со списком упражнений;
* результат за период времени — тренировки пользователя за выбранный период.

Бизнес-правила:

* тренировку нельзя создать без хотя бы одного упражнения;
* дата тренировки не может быть в будущем;
* подходы и повторения не могут быть меньше нуля;
* тип тренировки — только «кардио» или «силовая»;
* конец периода результата не может быть раньше его начала;
* отмена тренировки не удаляет её: объект остаётся в коллекции, а
  отменённая тренировка не учитывается в статистике и результатах.

## Основные сущности

### Exercise — упражнение

Атрибуты: `id`, `name`, `muscle_group`.
Методы: `is_for_muscle_group()` — проверка группы мышц; `__str__()`.

### User — пользователь

Атрибуты: `id`, `name`, `registered_at`.
Методы: `from_data()` (`@classmethod`) — создание из данных JSON; `__str__()`.

### WorkoutExercise — выполненное упражнение

Атрибуты: `exercise` (объект `Exercise`), `sets`, `reps`, `weight`.
Методы: `is_valid()`, `tonnage()`, `__str__()`.

### Workout, CardioWorkout, StrengthWorkout — тренировки

`Workout` — базовый класс. Атрибуты: `id`, `user` (объект `User`),
`workout_date`, `exercises` (список `WorkoutExercise`), `duration_min`,
`is_cancelled`. Методы: `cancel()`, `is_in_period()`, `is_valid_date()`
(`@staticmethod`), `__str__()`.
Подклассы `CardioWorkout` («кардио») и `StrengthWorkout` («силовая»)
переопределяют `__str__()`: кардио показывает длительность, силовая —
суммарный тоннаж.

### Result — результат за период

Атрибуты: `id`, `user` (объект `User`), `period_start`, `period_end`,
`workouts` (список объектов `Workout`).
Методы: `get_stats()` — статистика по неотменённым тренировкам; `__str__()`.

Объекты хранят ссылки друг на друга (`workout.user`,
`workout.exercises[i].exercise`, `result.workouts[i]`), поэтому и консольная,
и веб-версия работают с одними и теми же объектами.

## Страницы веб-интерфейса

| URL | Имя маршрута | View-функция | Шаблон |
|---|---|---|---|
| `/` | `homepage:index` | `homepage.views.index()` | `homepage/index.html` |
| `/exercises/` | `exercises:list` | `exercises.views.exercises()` | `exercises/exercise_list.html` |
| `/exercises/<int:exercise_id>/` | `exercises:detail` | `exercises.views.exercise_detail()` | `exercises/exercise_detail.html` |
| `/workouts/` | `workouts:list` | `workouts.views.workouts()` | `workouts/workout_list.html` |
| `/workouts/<int:workout_id>/` | `workouts:detail` | `workouts.views.workout_detail()` | `workouts/workout_detail.html` |

Если упражнение или тренировка с указанным идентификатором не найдены,
страница возвращает код статуса 404. Для любого адреса, которому не нашлось
маршрута, срабатывает обработчик `handler404` — собственная страница
«404 – страница не найдена» (`homepage.views.page_not_found()`, шаблон
`homepage/404.html`).

Маршрутизация двух уровней: корневой `workout_app/urls.py` подключает
маршруты приложений через `include()`, а конкретные адреса описаны в
`urls.py` каждого приложения.

## Веб-интерфейс и шаблоны Django

Веб-часть приложения реализована на Django. HTML формируется не в Python-коде,
а в шаблонах: view-функция получает данные, кладёт их в контекст и вызывает
`render()`. Функция `page()` из ПР5 больше не используется и удалена.

### Базовый шаблон и наследование

Общая структура всех страниц находится в `templates/base.html`: объявление
документа, кодировка, заголовок вкладки, Bootstrap, собственный CSS, логотип,
навигация, контейнер содержимого, подвал и подключение JavaScript. Дочерние
шаблоны подключают его через `{% extends "base.html" %}` и переопределяют
блоки `{% block title %}` и `{% block content %}`.

### Включаемые шаблоны

Повторяющиеся фрагменты вынесены в отдельные шаблоны и подключаются через
`{% include %}`:

* `templates/includes/navigation.html` — навигация (подключена в `base.html`);
* `exercises/includes/exercise_card.html` — карточка упражнения в списке;
* `workouts/includes/workout_status.html` — статус тренировки (активна или
  отменена) в списке и на странице тренировки.

### Контекст, циклы и условия

View-функции передают данные словарём контекста, например
`{"exercises": exercises_list}`, а шаблон обращается к ним по имени:
`{% for exercise in exercises %}`. Для пустых коллекций используется
`{% empty %}`, для разных состояний данных — `{% if %}` (отменённая и активная
тренировка, наличие или отсутствие объекта на странице детали).

### Именованные URL и пространства имён

В `urls.py` каждого приложения задан `app_name` и имена маршрутов
(`homepage:index`, `exercises:list`, `exercises:detail`, `workouts:list`,
`workouts:detail`). Ссылки в шаблонах строятся тегом `{% url %}`, например
`{% url 'exercises:detail' exercise.id %}`, а не записываются адресом вручную.

### Фильтры шаблонов

* `{{ exercises|length }}` — количество элементов списка;
* `{{ exercise.name|default:"Без названия" }}` — значение по умолчанию;
* `{{ workout.workout_date|date:"d.m.Y" }}` — формат даты.

Фильтры отвечают только за представление данных, бизнес-логика остаётся в
Python-коде (`models/`).

### Статические файлы

Статика находится в `homepage/static/homepage/`: `css/style.css` (собственные
стили карточек, статуса и логотипа), `js/main.js` (подстановка текущего года в
подвал), `img/logo.png` (логотип). В шаблонах используются `{% load static %}`
и `{% static %}`. Bootstrap сохранён для базовой вёрстки, собственный CSS его
дополняет.

### Данные

Источник данных не изменился: JSON-файлы и объекты классов ПР3 загружаются
функциями `storage.py`. Django ORM на этом этапе не используется.

## Основные операции

### Используется в веб-интерфейсе (ПР5–ПР6)

* просмотр списка упражнений;
* просмотр информации об упражнении (в скольких активных тренировках оно
  выполнялось);
* просмотр списка тренировок;
* просмотр информации о тренировке.

### Отложено до следующих работ

Эти операции реализованы в консольной версии (ПР3) и появятся в вебе, когда
будут добавлены формы и POST-запросы:

* добавление упражнения;
* поиск и фильтрация упражнений, сортировка;
* создание и отмена тренировки;
* формирование результата за период и статистика;
* создание, поиск и выбор пользователя.

## Хранение данных

Данные хранятся в JSON-файлах каталога `data/`:

* `data/exercises.json`;
* `data/users.json`;
* `data/workouts.json`;
* `data/results.json`.

При загрузке данные из JSON преобразуются в объекты, при сохранении объекты
преобразуются обратно в JSON. Связи между объектами хранятся как
идентификаторы (`user_id`, `exercise_id`, `workout_ids`). Если связанный
объект не найден, запись пропускается с предупреждением.
База данных Django на этом этапе не используется для данных проекта:
`manage.py migrate` создаёт только служебные таблицы Django (файл
`db.sqlite3`, он исключён из Git).

## Структура проекта

```text
workout_app/
│
├── README.md
├── requirements.txt
├── manage.py
├── main.py
├── storage.py
├── utils.py
├── conftest.py
│
├── workout_app/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── templates/
│   ├── base.html
│   └── includes/
│       └── navigation.html
│
├── homepage/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── static/
│   │   └── homepage/
│   │       ├── css/style.css
│   │       ├── img/logo.png
│   │       └── js/main.js
│   ├── templates/
│   │   └── homepage/
│   │       ├── 404.html
│   │       └── index.html
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── exercises/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── templates/
│   │   └── exercises/
│   │       ├── exercise_detail.html
│   │       ├── exercise_list.html
│   │       └── includes/
│   │           └── exercise_card.html
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── workouts/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── templates/
│   │   └── workouts/
│   │       ├── workout_detail.html
│   │       ├── workout_list.html
│   │       └── includes/
│   │           └── workout_status.html
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── models/
│   ├── __init__.py
│   ├── exercises.py
│   ├── users.py
│   ├── workouts.py
│   └── results.py
│
├── data/
│   ├── exercises.json
│   ├── users.json
│   ├── workouts.json
│   └── results.json
│
└── tests/
    ├── test_exercises.py
    ├── test_users.py
    ├── test_workouts.py
    ├── test_results.py
    ├── test_storage.py
    └── test_web.py
```

## Назначение модулей

### `main.py`

Консольная версия приложения (сохранена с ПР3): меню, ввод данных,
пользовательские сценарии.

### `workout_app/`

Пакет настроек Django-проекта:

* `settings.py` — настройки проекта (приложения, шаблоны — каталог
  `templates/` в `DIRS`, язык, часовой пояс, режим отладки, разрешённые хосты);
* `urls.py` — маршрутизация верхнего уровня и `handler404`;
* `asgi.py`, `wsgi.py` — точки взаимодействия с сервером.

### `homepage/`

Django-приложение главной страницы:

* `views.py` — view-функции `index()` и `page_not_found()`;
* `urls.py` — маршрут главной страницы (`app_name = "homepage"`);
* `templates/homepage/` — шаблоны главной страницы и страницы 404;
* `static/homepage/` — общие статические файлы проекта (CSS, JavaScript,
  логотип).

### `exercises/`

Django-приложение упражнений: `views.py` — `exercises()` и
`exercise_detail()`; `urls.py` — маршруты приложения (`app_name = "exercises"`);
`templates/exercises/` — шаблоны списка, страницы и карточки упражнения; `models.py` — Django-
модели (заполняется в следующих работах).

### `workouts/`

Django-приложение тренировок: `views.py` — `workouts()`, `workout_detail()`
и вспомогательная `load_all_workouts()`; `urls.py` — маршруты приложения
(`app_name = "workouts"`); `templates/workouts/` — шаблоны списка, страницы
и статуса тренировки;
`models.py` — Django-модели (заполняется в следующих работах).

Приложение для пользователей не создавалось: пользователь пока не имеет
веб-страниц, а работа с пользователями (регистрация, вход) рассматривается в
следующих темах.

### `models/`

Классы предметной области и функции работы с ними (пакет ПР3):
`exercises.py`, `users.py`, `workouts.py`, `results.py`.

### `templates/`

Шаблоны уровня проекта: `base.html` и `includes/navigation.html`.

### `storage.py`

Загрузка и сохранение данных: JSON → объекты и объекты → JSON.

### `utils.py`

Функции консольного ввода: `input_int()`, `input_date()`.

### `tests/`

Автоматизированные тесты проекта. `conftest.py` в корне подключает
настройки Django, чтобы `tests/test_web.py` мог проверять страницы.

## Запуск приложения

Подготовка окружения (один раз):

```text
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

Проверка конфигурации Django:

```text
python manage.py check
```

Веб-версия (Django):

```text
python manage.py runserver
```

После запуска открыть в браузере `http://127.0.0.1:8000/`.

Консольная версия (сохранена):

```text
python main.py
```

Настройка `DEBUG = True` подходит для разработки. Чтобы увидеть собственную
страницу 404 вместо технической страницы отладки, временно задайте
`DEBUG = False` (в `ALLOWED_HOSTS` уже указаны `localhost` и `127.0.0.1`) и
верните `True` после проверки.

## Тестирование

```text
pytest -v
```

Тесты покрывают сущности предметной области (`test_exercises.py`,
`test_users.py`, `test_workouts.py`, `test_results.py`), загрузку и
сохранение JSON (`test_storage.py`) и веб-слой: страницы, коды ответов и
страницу 404, базовый шаблон, статику и именованные URL (`test_web.py`).

## Проверка качества кода

```text
flake8 .
black . --check
```

Настройки `flake8` находятся в `.flake8`: длина строки 88 (как у `black`),
каталоги `venv/` и `migrations/` исключены, для `settings.py` отключена
проверка длины строк.

## Зависимости

Состав `requirements.txt`:

* `Django==5.2.*` — веб-фреймворк;
* `pytest` — автоматизированные тесты;
* `flake8` — линтер;
* `black` — форматтер.

## Текущее состояние и план развития

Реализовано (ПР5–ПР6):

* Django-проект и три приложения (`homepage`, `exercises`, `workouts`);
* маршрутизация двух уровней и обработка ошибки 404;
* view-функции и страницы со списками и страницами объектов;
* отображение данных предметной области из JSON через классы ПР3;
* Django Template Language: базовый шаблон `base.html`, наследование, блоки,
  включаемые шаблоны, контекст, циклы и условия, фильтры;
* именованные URL и пространства имён, ссылки через `{% url %}`;
* статические файлы: собственные CSS и JavaScript, логотип;
* навигация между страницами и оформление Bootstrap 5.3.

Пока не реализовано: формы, Django ORM и база данных для данных проекта
(данные по-прежнему хранятся в JSON).

Планируется:

* перенос сущностей в Django ORM, подключение базы данных;
* формы создания и отмены тренировок;
* использование отложенной логики ПР3 в веб-интерфейсе;
* регистрация и вход пользователей;
* разработка API, контейнеризация, настройка CI/CD.

## Функции проекта по файлам

Сущность Exercise (ПР3):

| Имя | Файл | Назначение |
|---|---|---|
| `Exercise` (класс) | `models/exercises.py` | упражнение: `id`, `name`, `muscle_group` |
| `is_for_muscle_group()` | `models/exercises.py` | проверка группы мышц |
| `add_exercise()` | `models/exercises.py` | создание упражнения и добавление в коллекцию |
| `find_exercise()` | `models/exercises.py` | поиск по названию |
| `find_exercise_by_id()` | `models/exercises.py` | поиск по id; используется страницей упражнения |
| `filter_exercises_by_muscle_group()` | `models/exercises.py` | отбор по группе мышц |
| `sort_exercises()` | `models/exercises.py` | сортировка по названию; используется списком упражнений |
| `show_exercises()` | `models/exercises.py` | вывод в консоль |

Сущность User (ПР3):

| Имя | Файл | Назначение |
|---|---|---|
| `User` (класс) | `models/users.py` | пользователь: `id`, `name`, `registered_at` |
| `from_data()` | `models/users.py` | создание объекта из данных JSON |
| `add_user()`, `find_user()`, `find_user_by_id()`, `show_users()` | `models/users.py` | работа с коллекцией пользователей |

Сущность Workout (ПР3, функция `find_workouts_with_exercise()` добавлена в ПР5):

| Имя | Файл | Назначение |
|---|---|---|
| `WorkoutExercise` (класс) | `models/workouts.py` | выполненное упражнение: подходы, повторения, вес |
| `Workout`, `CardioWorkout`, `StrengthWorkout` | `models/workouts.py` | тренировки (наследование, переопределённый `__str__`) |
| `create_workout()` | `models/workouts.py` | проверка правил, создание и добавление тренировки |
| `cancel_workout()` | `models/workouts.py` | отмена без удаления |
| `find_workout_by_id()` | `models/workouts.py` | поиск по id; используется страницей тренировки |
| `find_workouts_with_exercise()` | `models/workouts.py` | активные тренировки с упражнением; используется страницей упражнения (ПР5) |
| `find_workouts_in_period()`, `get_user_workouts()`, `get_workout_stats()`, `show_workouts()` | `models/workouts.py` | отбор, статистика, вывод |
| `reality_task()`, `trening_result()` | `models/workouts.py` | функции из ПР1 |

Сущность Result (ПР3):

| Имя | Файл | Назначение |
|---|---|---|
| `Result` (класс) | `models/results.py` | результат за период, метод `get_stats()` |
| `create_result()`, `find_result_by_id()`, `get_user_results()`, `show_results()` | `models/results.py` | работа с результатами |

Хранение данных (ПР3):

| Имя | Файл | Назначение |
|---|---|---|
| `load_exercises()`, `save_exercises()` | `storage.py` | JSON ↔ объекты `Exercise`; используется вебом |
| `load_users()`, `save_users()` | `storage.py` | JSON ↔ объекты `User`; используется вебом |
| `load_workouts()`, `save_workouts()` | `storage.py` | JSON ↔ объекты `Workout`; используется вебом |
| `load_results()`, `save_results()` | `storage.py` | JSON ↔ объекты `Result` |

Веб-слой (ПР5–ПР6, HTML формируется шаблонами через `render()`):

| Имя | Файл | Назначение |
|---|---|---|
| `index()` | `homepage/views.py` | главная страница `/` |
| `page_not_found()` | `homepage/views.py` | обработчик 404 |
| `exercises()` | `exercises/views.py` | страница `/exercises/` |
| `exercise_detail()` | `exercises/views.py` | страница `/exercises/<id>/`, код 404 если не найдено |
| `workouts()` | `workouts/views.py` | страница `/workouts/` |
| `workout_detail()` | `workouts/views.py` | страница `/workouts/<id>/`, код 404 если не найдено |
| `load_all_workouts()` | `workouts/views.py` | загрузка тренировок со связанными объектами |

Функции сущностей и хранилища используются и консольной, и веб-версией:
view-функции вызывают `load_*()` и `find_*_by_id()` вместо консольных
сценариев `main.py`.
