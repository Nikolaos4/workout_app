# Сервис учета тренировок

## Назначение

Приложение для учета тренировок: пользователь записывает тренировки,
отслеживает прогресс, анализирует нагрузку и видит динамику результатов.
Консольная версия приложения (ПР1–ПР3) дополнена веб-интерфейсом на Django
(ПР5), страницы которого с ПР6 строятся на шаблонах Django. С ПР7 данные
веб-интерфейса берутся из базы данных SQLite через SQL-запросы.

Приложение позволяет:

* просматривать упражнения в браузере;
* просматривать информацию об отдельном упражнении и о том, в скольких
  тренировках оно выполнялось;
* искать упражнения по группе мышц и части названия;
* просматривать список тренировок в браузере и фильтровать его по периоду
  дат и признаку «только активные»;
* просматривать информацию об отдельной тренировке, её пользователе и
  выполненных упражнениях;
* просматривать статистику по активным тренировкам: сводку, популярность
  упражнений, тоннаж по группам мышц, активных пользователей;
* в консольной версии: добавлять упражнения, искать и фильтровать их,
  создавать и отменять тренировки, формировать результат за период,
  смотреть статистику, работать с пользователями;
* хранить данные между запусками приложения в JSON-файлах (консольная
  версия) и в базе данных SQLite (веб-интерфейс).

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
* SQLite и модуль `sqlite3` стандартной библиотеки — реляционная база
  данных и SQL-запросы (ПР7);
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
| `/exercises/search/` | `exercises:search` | `exercises.views.exercise_search()` | `exercises/exercise_search.html` |
| `/exercises/<int:exercise_id>/` | `exercises:detail` | `exercises.views.exercise_detail()` | `exercises/exercise_detail.html` |
| `/workouts/` | `workouts:list` | `workouts.views.workouts()` | `workouts/workout_list.html` |
| `/workouts/statistics/` | `workouts:statistics` | `workouts.views.statistics()` | `workouts/statistics.html` |
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

С ПР7 view-функции получают данные не из JSON, а из базы SQLite запросами
`sqlite3` (подробнее — в разделе «База данных SQLite»). Результат запроса
(`sqlite3.Row`) передаётся в шаблон через контекст, поля доступны по именам:
`{{ workout.user_name }}`. Django ORM на этом этапе не используется.

## Основные операции

### Используется в веб-интерфейсе (ПР5–ПР7)

* просмотр списка упражнений;
* просмотр информации об упражнении (в скольких активных тренировках оно
  выполнялось);
* поиск упражнений по группе мышц и части названия (ПР7);
* просмотр списка тренировок с фильтрами по периоду и признаку (ПР7);
* просмотр информации о тренировке;
* статистика по активным тренировкам (ПР7).

### Отложено до следующих работ

Эти операции реализованы в консольной версии (ПР3) и появятся в вебе, когда
будут добавлены формы и POST-запросы:

* добавление упражнения;
* создание и отмена тренировки;
* формирование и сохранение результата за период;
* создание, поиск и выбор пользователя.

## Хранение данных

Исходные данные проекта лежат в JSON-файлах каталога `data/`:

* `data/exercises.json`;
* `data/users.json`;
* `data/workouts.json`;
* `data/results.json`.

JSON-хранилище ПР1–ПР6 сохранено: консольная версия (`main.py`) и
`storage.py` по-прежнему работают с JSON и объектами классов ПР3. Для
веб-интерфейса с ПР7 используется база данных SQLite (см. ниже), а JSON-файлы
служат источником для её заполнения.

База данных Django на этом этапе не используется для данных проекта:
`manage.py migrate` создаёт только служебные таблицы Django (файл
`db.sqlite3`, он исключён из Git).

## База данных SQLite (ПР7)

Файл базы данных проекта — `data/workout_app.sqlite` (отдельный от служебного
`db.sqlite3` Django). Работа с ним ведётся напрямую через `sqlite3` и
SQL-запросы, без Django ORM.

### Таблицы

**`users`** — пользователи

| Поле | Тип | Назначение |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `name` | TEXT, NOT NULL | имя |
| `registered_at` | TEXT, NOT NULL | дата регистрации, `YYYY-MM-DD` |

**`exercises`** — справочник упражнений

| Поле | Тип | Назначение |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `name` | TEXT, NOT NULL | название |
| `muscle_group` | TEXT, NOT NULL | группа мышц |

**`workouts`** — тренировки

| Поле | Тип | Назначение |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `user_id` | INTEGER, NOT NULL, FOREIGN KEY → `users.id` | пользователь |
| `workout_date` | TEXT, NOT NULL | дата, `YYYY-MM-DD` |
| `workout_type` | TEXT, NOT NULL, CHECK | «кардио» или «силовая» |
| `duration_min` | INTEGER, NOT NULL, DEFAULT 0 | длительность в минутах |
| `is_cancelled` | INTEGER, NOT NULL, DEFAULT 0 | 0 — активна, 1 — отменена |

**`workout_exercises`** — выполненные упражнения тренировки (связь «многие ко
многим» между `workouts` и `exercises`; в JSON это вложенный список
`exercises`)

| Поле | Тип | Назначение |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `workout_id` | INTEGER, NOT NULL, FOREIGN KEY → `workouts.id` | тренировка |
| `exercise_id` | INTEGER, NOT NULL, FOREIGN KEY → `exercises.id` | упражнение |
| `sets` | INTEGER, NOT NULL, CHECK >= 0 | подходы |
| `reps` | INTEGER, NOT NULL, CHECK >= 0 | повторения |
| `weight` | REAL, NOT NULL, DEFAULT 0 | вес, кг |

**`results`** — результаты за период

| Поле | Тип | Назначение |
|---|---|---|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `user_id` | INTEGER, NOT NULL, FOREIGN KEY → `users.id` | пользователь |
| `period_start`, `period_end` | TEXT, NOT NULL | границы периода (конец не раньше начала) |

**`result_workouts`** — тренировки, вошедшие в результат (в JSON — список
`workout_ids`). Составной первичный ключ (`result_id`, `workout_id`), оба
поля — внешние ключи на `results.id` и `workouts.id`.

Связи: у пользователя много тренировок и результатов; тренировка состоит из
нескольких выполненных упражнений; результат включает несколько тренировок.
Значения NULL в таблицах не допускаются: все поля обязательны (необязательное
в JSON `duration_min` при импорте получает значение по умолчанию 0).
Логическое значение `is_cancelled` хранится числом 0/1, даты — строками
`YYYY-MM-DD`, поэтому их можно сравнивать и сортировать средствами SQL.

### Файлы слоя базы данных

* `sql/schema.sql` — команды создания таблиц (`CREATE TABLE IF NOT EXISTS`,
  выполняются повторно без ошибок);
* `sql/queries.sql` — проверенные SQL-запросы проекта с комментариями;
* `sql/demo_data.sql` — необязательные демонстрационные данные поверх
  импорта (для проверки фильтров, статистики и `HAVING`);
* `db/database.py` — `get_connection()` (подключение и
  `PRAGMA foreign_keys = ON`) и `init_db()` (применение схемы);
* `db/import_json.py` — перенос данных из JSON в таблицы;
* `data/workout_app.sqlite` — файл базы данных.

### Создание базы и перенос данных

Из корня проекта:

```text
python -m db.import_json
```

Команда создаёт файл базы и таблицы (если их ещё нет), очищает таблицы и
переносит данные из JSON через `executemany()` в одной транзакции
(`commit()` при успехе, `rollback()` при ошибке). Порядок импорта важен:
сначала `users` и `exercises`, затем `workouts` и `workout_exercises`, затем
`results` и `result_workouts` — иначе внешние ключи ссылались бы на ещё не
существующие записи. Повторный запуск возвращает базу к состоянию JSON.

Отдельно схему можно применить так:

```text
python -c "import sqlite3; c=sqlite3.connect('data/workout_app.sqlite'); c.executescript(open('sql/schema.sql', encoding='utf-8').read()); c.commit(); c.close()"
```

Проверка в SQLite CLI:

```text
sqlite3 data/workout_app.sqlite
sqlite> .tables
sqlite> SELECT COUNT(*) FROM workouts;
```

Запросы из `sql/queries.sql` можно выполнить все сразу:
`sqlite3 -header -column data/workout_app.sqlite < sql/queries.sql`.
Демо-данные: `sqlite3 data/workout_app.sqlite < sql/demo_data.sql`
(один раз; вернуться к данным JSON — `python -m db.import_json`).

### SQL-запросы проекта

В `sql/queries.sql` — 16 запросов (запросы 1–4 и 6–13 используются
веб-приложением, 5 и 14–16 — для проверки в SQLite CLI):

| № | Назначение | Вид | Где используется |
|---|---|---|---|
| 1 | список упражнений | SELECT, ORDER BY | `exercises()` |
| 2 | группы мышц без повторов | SELECT DISTINCT | `exercise_search()` |
| 3 | упражнение по id | WHERE | `exercise_detail()` |
| 4 | поиск по группе мышц и названию | WHERE, LIKE, параметры | `exercise_search()` |
| 5 | активные тренировки за период | WHERE, BETWEEN | проверка в CLI |
| 6 | список тренировок с пользователем, числом упражнений и тоннажем | JOIN, LEFT JOIN, GROUP BY, параметры | `workouts()` |
| 7 | тренировка с пользователем | JOIN, WHERE | `workout_detail()` |
| 8 | упражнения тренировки с тоннажем | JOIN | `workout_detail()` |
| 9 | сводка по активным тренировкам | COUNT, AVG, MIN, MAX | `statistics()` |
| 10 | в скольких тренировках выполнялось упражнение | COUNT(DISTINCT), JOIN | `exercise_detail()` |
| 11 | популярность упражнений | LEFT JOIN, GROUP BY, COUNT | `statistics()` |
| 12 | тоннаж по группам мышц | JOIN, SUM, GROUP BY | `statistics()` |
| 13 | пользователи с числом тренировок не меньше N | GROUP BY, HAVING, параметры | `statistics()` |
| 14 | число записей в таблицах (сверка с JSON) | COUNT, UNION ALL | проверка в CLI |
| 15 | постраничный вывод тренировок | ORDER BY, LIMIT, OFFSET | проверка в CLI |
| 16 | упражнения, которых не было ни в одной тренировке | подзапрос NOT IN | проверка в CLI |

### Получение данных в Django-представлениях

Представления открывают соединение функцией `get_connection()`, задают
`conn.row_factory = sqlite3.Row` (строки результата доступны по именам
столбцов: `row["name"]` в Python и `{{ row.name }}` в шаблоне, без привязки
к порядку столбцов в запросе), выполняют запрос, получают `fetchall()` или
`fetchone()` и закрывают соединение. Значения из URL и форм передаются только
параметрами (`?` и `:имя`), а не подстановкой в строку SQL: так пользовательский
ввод не может изменить текст запроса. Пустой результат запроса — не ошибка:
шаблон показывает сообщение через `{% empty %}`.

Страницы, данные которых приходят из SQLite: `/exercises/`,
`/exercises/<id>/`, `/exercises/search/`, `/workouts/`, `/workouts/<id>/`,
`/workouts/statistics/` (главная страница статических данных не содержит).

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
│   │       ├── exercise_search.html
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
│   │       ├── statistics.html
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
├── db/
│   ├── __init__.py
│   ├── database.py
│   └── import_json.py
│
├── sql/
│   ├── schema.sql
│   ├── queries.sql
│   └── demo_data.sql
│
├── data/
│   ├── exercises.json
│   ├── users.json
│   ├── workouts.json
│   ├── results.json
│   └── workout_app.sqlite
│
└── tests/
    ├── test_exercises.py
    ├── test_users.py
    ├── test_workouts.py
    ├── test_results.py
    ├── test_storage.py
    ├── test_db.py
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

Django-приложение упражнений: `views.py` — `exercises()`,
`exercise_detail()` и `exercise_search()` (данные из SQLite); `urls.py` — маршруты приложения (`app_name = "exercises"`);
`templates/exercises/` — шаблоны списка, страницы и карточки упражнения; `models.py` — Django-
модели (заполняется в следующих работах).

### `workouts/`

Django-приложение тренировок: `views.py` — `workouts()`, `workout_detail()`
и `statistics()` (данные из SQLite); `urls.py` — маршруты приложения
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

### `db/` и `sql/`

Слой базы данных (ПР7): `db/database.py` — подключение к SQLite,
`db/import_json.py` — перенос данных из JSON, `sql/schema.sql` — схема,
`sql/queries.sql` — запросы, `sql/demo_data.sql` — демонстрационные данные.

### `storage.py`

Загрузка и сохранение данных: JSON → объекты и объекты → JSON (используется
консольной версией; веб-интерфейс с ПР7 работает с SQLite).

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
Слой SQLite проверяет `test_db.py`: создание схемы и её повторное
применение, внешние ключи и `CHECK`, импорт из JSON (совпадение числа
записей, повторный запуск), страницы с данными из базы, фильтры, поиск,
`HAVING`, пустые результаты и защиту от SQL-инъекции. Тесты работают с
временной базой, рабочий файл `data/workout_app.sqlite` не изменяется.

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

Реализовано (ПР5–ПР7):

* Django-проект и три приложения (`homepage`, `exercises`, `workouts`);
* маршрутизация двух уровней и обработка ошибки 404;
* view-функции и страницы со списками и страницами объектов;
* отображение данных предметной области из JSON через классы ПР3
  (консольная версия);
* база данных SQLite: схема, первичные и внешние ключи, перенос данных
  из JSON, SQL-запросы (`WHERE`, `JOIN`, `COUNT`, `GROUP BY`, `HAVING`),
  получение данных в представлениях (ПР7);
* страницы поиска упражнений, фильтра тренировок и статистики (ПР7);
* Django Template Language: базовый шаблон `base.html`, наследование, блоки,
  включаемые шаблоны, контекст, циклы и условия, фильтры;
* именованные URL и пространства имён, ссылки через `{% url %}`;
* статические файлы: собственные CSS и JavaScript, логотип;
* навигация между страницами и оформление Bootstrap 5.3.

Пока не реализовано: формы, Django ORM и модели Django (база SQLite
используется напрямую через `sqlite3`).

Планируется:

* перенос сущностей в Django ORM и модели Django, подключение базы данных
  к Django;
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

Веб-слой (ПР5–ПР7, HTML формируется шаблонами через `render()`, данные
из SQLite):

| Имя | Файл | Назначение |
|---|---|---|
| `index()` | `homepage/views.py` | главная страница `/` |
| `page_not_found()` | `homepage/views.py` | обработчик 404 |
| `exercises()` | `exercises/views.py` | страница `/exercises/` |
| `exercise_detail()` | `exercises/views.py` | страница `/exercises/<id>/`, код 404 если не найдено |
| `exercise_search()` | `exercises/views.py` | страница `/exercises/search/`, поиск по параметрам |
| `workouts()` | `workouts/views.py` | страница `/workouts/` |
| `workout_detail()` | `workouts/views.py` | страница `/workouts/<id>/`, код 404 если не найдено |
| `statistics()` | `workouts/views.py` | страница `/workouts/statistics/` |
| `get_connection()`, `init_db()` | `db/database.py` | подключение к SQLite, применение схемы |
| `import_all()` и функции `import_*()` | `db/import_json.py` | перенос данных из JSON в SQLite |

Классы и функции ПР3 используются консольной версией. Веб-представления
с ПР7 получают данные SQL-запросами к SQLite и не вызывают `load_*()`
и `find_*_by_id()`, но структура таблиц повторяет те же сущности.
