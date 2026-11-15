"""View-функции приложения workouts: данные берутся через Django ORM (ПР9)."""

from datetime import date

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, FloatField, Max, Min, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from exercises.models import Exercise
from users.models import User

from .models import Workout, WorkoutExercise

# Сколько тренировок показывать на одной странице списка.
PAGE_SIZE = 5

# Допустимые значения параметра sort. В order_by() попадают только поля из
# этого словаря, а не произвольная строка из запроса пользователя.
SORT_FIELDS = {
    "date": ("-workout_date", "-pk"),
    "date_asc": ("workout_date", "pk"),
    "user": ("user__name", "-workout_date", "-pk"),
    "duration": ("-duration_min", "-pk"),
    "tonnage": ("-tonnage", "-pk"),
}
SORT_LABELS = {
    "date": "дате (сначала новые)",
    "date_asc": "дате (сначала старые)",
    "user": "пользователю",
    "duration": "длительности",
    "tonnage": "тоннажу",
}
DEFAULT_SORT = "date"


def _parse_date(value):
    """Вернуть дату или None, если строка не в формате ГГГГ-ММ-ДД."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_id(value):
    """Вернуть целый идентификатор из строки или None, если это не число."""
    if value.isascii() and value.isdigit() and len(value) <= 9:
        return int(value)
    return None


def _tonnage(prefix=""):
    """Сумма «подходы × повторения × вес»; prefix — путь до строк упражнений."""
    return Sum(
        F(f"{prefix}sets") * F(f"{prefix}reps") * F(f"{prefix}weight"),
        output_field=FloatField(),
    )


def workouts(request):
    """Страница /workouts/: список тренировок с фильтрами, сортировкой и страницами.

    GET-параметры: active=1 (только активные), start и end (период дат),
    q (поиск по имени пользователя и типу), type, user, sort, page.
    """
    only_active = request.GET.get("active") == "1"
    start_raw = request.GET.get("start", "")
    end_raw = request.GET.get("end", "")
    query = request.GET.get("q", "").strip()
    type_raw = request.GET.get("type", "")
    user_raw = request.GET.get("user", "")
    sort = request.GET.get("sort", DEFAULT_SORT)
    if sort not in SORT_FIELDS:
        sort = DEFAULT_SORT

    start = _parse_date(start_raw) if start_raw else None
    end = _parse_date(end_raw) if end_raw else None
    invalid_dates = (start_raw and start is None) or (end_raw and end is None)

    # select_related загружает пользователя тем же запросом (JOIN), а
    # annotate считает для каждой тренировки число упражнений и тоннаж.
    # Тренировки без упражнений остаются в списке (с нулями).
    queryset = Workout.objects.select_related("user").annotate(
        exercises_count=Count("workout_exercises"),
        tonnage=Coalesce(
            _tonnage("workout_exercises__"), 0.0, output_field=FloatField()
        ),
    )

    if only_active:
        queryset = queryset.filter(is_cancelled=False)
    if start:
        queryset = queryset.filter(workout_date__gte=start)
    if end: 
        queryset = queryset.filter(workout_date__lte=end)
    if query:
        # Поиск по нескольким полям, в том числе по полю связанной модели.
        queryset = queryset.filter(
            Q(user__name__icontains=query) | Q(workout_type__icontains=query)
        )
    if type_raw in Workout.WorkoutType.values:
        queryset = queryset.filter(workout_type=type_raw)
    user_id = _parse_id(user_raw)
    if user_id is not None:
        queryset = queryset.filter(user_id=user_id)
    if invalid_dates:
        queryset = Workout.objects.none()

    paginator = Paginator(queryset.order_by(*SORT_FIELDS[sort]), PAGE_SIZE)
    # get_page не падает: неверный номер страницы заменяется ближайшим верным.
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "workouts": page_obj,
        "page_obj": page_obj,
        "total": paginator.count,
        "only_active": only_active,
        "start": start_raw,
        "end": end_raw,
        "q": query,
        "selected_type": type_raw,
        "selected_user": user_raw,
        "sort": sort,
        "sort_options": SORT_LABELS.items(),
        "workout_types": Workout.WorkoutType.choices,
        "users": User.objects.order_by("name"),
        "invalid_dates": invalid_dates,
    }

    return render(
        request,
        "workouts/workout_list.html",
        context,
    )


def workout_detail(request, workout_id):
    """Страница /workouts/<id>/: информация о тренировке.

    Если тренировка не найдена, шаблон показывает сообщение об этом,
    а ответ возвращается с кодом 404.
    """
    items = []
    try:
        workout = Workout.objects.select_related("user").get(pk=workout_id)
    except Workout.DoesNotExist:
        workout = None
    else:
        # Строки упражнений вместе с упражнениями одним запросом (JOIN).
        items = workout.workout_exercises.select_related("exercise").order_by("pk")

    context = {
        "workout": workout,
        "items": items,
    }

    return render(
        request,
        "workouts/workout_detail.html",
        context,
        status=404 if workout is None else 200,
    )


def statistics(request):
    """Страница /workouts/statistics/: статистика по активным тренировкам.

    GET-параметр min_workouts задаёт порог для отбора пользователей.
    """
    try:
        min_workouts = min(max(int(request.GET.get("min_workouts", 1)), 0), 1_000_000)
    except ValueError:
        min_workouts = 1

    active_workouts = Workout.objects.filter(is_cancelled=False)

    # aggregate: один сводный показатель на весь набор.
    summary = active_workouts.aggregate(
        workouts_count=Count("id"),
        avg_duration=Avg("duration_min"),
        first_date=Min("workout_date"),
        last_date=Max("workout_date"),
    )

    # annotate: показатель для каждого упражнения. Упражнения без активных
    # тренировок остаются в списке с нулём; отменённые не учитываются.
    exercise_popularity = Exercise.objects.annotate(
        workouts_count=Count(
            "workout_exercises__workout",
            filter=Q(workout_exercises__workout__is_cancelled=False),
            distinct=True,
        )
    ).order_by("-workouts_count", "name")

    # values + annotate: группировка по группе мышц.
    muscle_group_tonnage = (
        WorkoutExercise.objects.filter(workout__is_cancelled=False)
        .values(muscle_group=F("exercise__muscle_group"))
        .annotate(tonnage=_tonnage())
        .order_by("-tonnage")
    )

    # Условие по активным тренировкам стоит до annotate, поэтому считаются
    # только они; фильтр по workouts_count после annotate работает как HAVING.
    active_users = (
        User.objects.filter(workouts__is_cancelled=False)
        .annotate(
            workouts_count=Count("workouts"),
            total_minutes=Sum("workouts__duration_min"),
        )
        .filter(workouts_count__gte=min_workouts)
        .order_by("-workouts_count", "name")
    )

    context = {
        "summary": summary,
        "exercise_popularity": exercise_popularity,
        "muscle_group_tonnage": muscle_group_tonnage,
        "active_users": active_users,
        "min_workouts": min_workouts,
    }

    return render(
        request,
        "workouts/statistics.html",
        context,
    )
