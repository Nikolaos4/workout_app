"""View-функции приложения exercises: данные берутся через Django ORM (ПР9)."""

from django.shortcuts import render

from .models import Exercise


def exercises(request):
    """Страница /exercises/: список упражнений, отсортированный по названию."""
    exercises_list = Exercise.objects.order_by("name")

    context = {
        "exercises": exercises_list,
    }

    return render(
        request,
        "exercises/exercise_list.html",
        context,
    )


def exercise_detail(request, exercise_id):
    """Страница /exercises/<id>/: информация об упражнении.

    Если упражнение не найдено, шаблон показывает сообщение об этом,
    а ответ возвращается с кодом 404.
    """
    used_count = 0
    same_group = Exercise.objects.none()

    try:
        exercise = Exercise.objects.get(pk=exercise_id)
    except Exercise.DoesNotExist:
        exercise = None
    else:
        # Обратная связь M2M (related_name="workouts"): в скольких активных
        # тренировках выполнялось упражнение. distinct() не даёт посчитать
        # тренировку дважды, если упражнение повторяется в ней несколько раз.
        used_count = exercise.workouts.filter(is_cancelled=False).distinct().count()
        # Другие упражнения той же группы мышц: исключаем текущее.
        same_group = (
            Exercise.objects.filter(muscle_group=exercise.muscle_group)
            .exclude(pk=exercise.pk)
            .order_by("name")
        )

    context = {
        "exercise": exercise,
        "used_count": used_count,
        "same_group": same_group,
    }

    return render(
        request,
        "exercises/exercise_detail.html",
        context,
        status=404 if exercise is None else 200,
    )


def exercise_search(request):
    """Страница /exercises/search/: поиск по группе мышц и названию.

    Значения из GET-параметров передаются в ORM-фильтры, которые сами
    подставляют их параметрами запроса, поэтому изменить текст SQL нельзя.
    Ограничение SQLite: оператор LIKE (а с ним и icontains) не различает
    регистр только у латинских букв, у кириллицы регистр учитывается.
    """
    muscle_group = request.GET.get("muscle_group", "")
    name = request.GET.get("name", "").strip()
    found = Exercise.objects.none()

    # Список групп мышц без повторов для выпадающего списка.
    muscle_groups = (
        Exercise.objects.order_by("muscle_group")
        .values_list("muscle_group", flat=True)
        .distinct()
    )

    if muscle_group:
        found = Exercise.objects.filter(
            muscle_group=muscle_group,
            name__icontains=name,
        ).order_by("name")

    context = {
        "muscle_groups": muscle_groups,
        "muscle_group": muscle_group,
        "name": name,
        "exercises": found,
    }

    return render(
        request,
        "exercises/exercise_search.html",
        context,
    )
