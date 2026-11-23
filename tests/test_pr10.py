import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from exercises.models import Exercise
from workouts.models import Workout

pytestmark = pytest.mark.django_db


def test_slug_route_and_unique_russian_names(base_data):
    a = Exercise.objects.create(name="Новое", muscle_group="Ноги")
    b = Exercise.objects.create(name="Новое", muscle_group="Ноги")
    assert a.slug and a.slug != b.slug
    response = Client(HTTP_HOST="localhost").get(a.get_absolute_url())
    assert response.status_code == 200
    assert a.name in response.content.decode()


def test_status_queries_and_statistics(base_data):
    workout = base_data.workout
    workout.status = Workout.Status.COMPLETED
    workout.save()
    assert Workout.objects.completed().for_date(workout.workout_date).count() == 1
    assert Workout.objects.active().count() == 0
    response = Client(HTTP_HOST="localhost").get("/workouts/statistics/")
    assert response.context["status_summary"]["completed"] == 1
    assert response.context["summary"]["workouts_count"] == 1
    workout.cancel()
    assert Workout.objects.cancelled().count() == 1
    assert Workout.objects.counted().count() == 0


def test_admin_access_lists_and_inlines(base_data):
    client = Client(HTTP_HOST="localhost")
    url = reverse("admin:workouts_workout_changelist")
    assert client.get(url).status_code == 302
    user = get_user_model().objects.create_superuser(
        "admin", password="temporary-test-only"
    )
    client.force_login(user)
    for name in (
        "exercises_exercise",
        "users_user",
        "workouts_workout",
        "results_result",
    ):
        assert client.get(reverse(f"admin:{name}_changelist")).status_code == 200
    assert (
        client.get(
            reverse("admin:users_user_change", args=[base_data.user.pk])
        ).status_code
        == 200
    )
    assert (
        client.get(
            reverse("admin:workouts_workout_change", args=[base_data.workout.pk])
        ).status_code
        == 200
    )


def test_admin_cancel_action(base_data):
    client = Client(HTTP_HOST="localhost")
    user = get_user_model().objects.create_superuser(
        "admin", password="temporary-test-only"
    )
    client.force_login(user)
    response = client.post(
        reverse("admin:workouts_workout_changelist"),
        {
            "action": "cancel_workouts",
            "_selected_action": [base_data.workout.pk],
        },
    )
    assert response.status_code == 302
    base_data.workout.refresh_from_db()
    assert base_data.workout.is_cancelled


def test_staff_without_permissions_cannot_view_workouts(base_data):
    user = get_user_model().objects.create_user("staff", is_staff=True)
    client = Client(HTTP_HOST="localhost")
    client.force_login(user)
    assert client.get(reverse("admin:workouts_workout_changelist")).status_code == 403
