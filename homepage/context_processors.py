from exercises.models import Exercise


def site_context(request):
    return {
        "site_name": "Сервис учета тренировок",
        "exercise_count": Exercise.objects.count(),
    }
