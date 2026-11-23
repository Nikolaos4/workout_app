"""ПР11: формы, атомарное сохранение, редактирование, POST/CSRF и изображения."""

from datetime import timedelta
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from exercises.forms import ExerciseForm
from exercises.models import Exercise
from workouts.forms import WorkoutFilterForm, WorkoutForm
from workouts.models import Workout, WorkoutExercise

pytestmark = pytest.mark.django_db


def browser(csrf=False):
    return Client(HTTP_HOST="localhost", enforce_csrf_checks=csrf)


def payload(base_data, rows=1):
    data = {
        "user": str(base_data.user.pk),
        "workout_date": timezone.localdate().isoformat(),
        "workout_type": "силовая",
        "duration_min": "45",
        "items-TOTAL_FORMS": str(rows),
        "items-INITIAL_FORMS": "0",
        "items-MIN_NUM_FORMS": "0",
        "items-MAX_NUM_FORMS": "30",
    }
    for i in range(rows):
        data.update(
            {
                f"items-{i}-exercise": str(base_data.bench.pk),
                f"items-{i}-sets": "3",
                f"items-{i}-reps": "10",
                f"items-{i}-weight": "40",
            }
        )
    return data


def test_filter_form_types_period_and_errors(base_data):
    form = WorkoutFilterForm({"start": "2026-09-01", "user": "1", "active": "1"})
    assert form.is_valid()
    assert form.cleaned_data["start"].year == 2026
    assert form.cleaned_data["user"] == 1
    assert form.cleaned_data["active"] is True
    form = WorkoutFilterForm({"start": "2026-10-01", "end": "2026-09-01"})
    assert not form.is_valid()
    assert form.non_field_errors()
    response = browser().get("/workouts/", {"start": "2026-10-01", "end": "2026-09-01"})
    assert response.status_code == 200
    assert response.context["total"] == 0
    assert "Начало периода" in response.content.decode()


@pytest.mark.parametrize(
    "url",
    [
        "/workouts/create/",
        "/workouts/1/edit/",
        "/exercises/create/",
        "/exercises/1/edit/",
    ],
)
def test_get_forms_does_not_write(base_data, url):
    before = (
        Workout.objects.count(),
        Exercise.objects.count(),
        WorkoutExercise.objects.count(),
    )
    response = browser().get(url)
    assert response.status_code == 200
    assert "csrfmiddlewaretoken" in response.content.decode()
    assert before == (
        Workout.objects.count(),
        Exercise.objects.count(),
        WorkoutExercise.objects.count(),
    )


def test_create_workout_with_two_rows_and_prg(base_data):
    data = payload(base_data, rows=2)
    data["status"] = "completed"  # Не входит в ModelForm, подмена игнорируется.
    response = browser().post("/workouts/create/", data)
    assert response.status_code == 302
    workout = Workout.objects.latest("pk")
    assert workout.status == Workout.Status.ACTIVE
    assert workout.duration_min == 45
    assert workout.workout_exercises.count() == 2
    assert response.url == reverse("workouts:detail", args=[workout.pk])


@pytest.mark.parametrize(
    "field,value",
    [
        ("user", "999999"),
        ("workout_type", "йога"),
        ("duration_min", "-1"),
        ("workout_date", "ошибка"),
        ("workout_date", ""),
        ("items-0-sets", "-1"),
        ("items-0-reps", "-2"),
        ("items-0-weight", "-5"),
        ("items-0-weight", "nan"),
        ("items-0-exercise", "999999"),
    ],
)
def test_invalid_create_keeps_bound_form_and_does_not_write(base_data, field, value):
    data = payload(base_data)
    data[field] = value
    before = (Workout.objects.count(), WorkoutExercise.objects.count())
    response = browser().post("/workouts/create/", data)
    assert response.status_code == 200
    assert response.context["form"].is_bound
    assert response.context["form"].errors or response.context["formset"].errors
    assert response.context["form"]["duration_min"].value() == data["duration_min"]
    assert before == (Workout.objects.count(), WorkoutExercise.objects.count())


def test_future_date_rejected_at_create_and_edit(base_data):
    data = payload(base_data)
    data["workout_date"] = (timezone.localdate() + timedelta(days=1)).isoformat()
    for url in ["/workouts/create/", "/workouts/1/edit/"]:
        response = browser().post(url, data)
        assert response.status_code == 200
        assert "workout_date" in response.context["form"].errors
    base_data.workout.refresh_from_db()
    assert base_data.workout.workout_date.year == 2026


def test_at_least_one_exercise_and_management_required(base_data):
    for data in [payload(base_data, rows=0), {"user": "1"}]:
        before = Workout.objects.count()
        response = browser().post("/workouts/create/", data)
        assert response.status_code == 200
        assert response.context["formset"].non_form_errors()
        assert Workout.objects.count() == before


def test_edit_updates_same_record_rows_and_preserves_status(base_data):
    base_data.workout.status = Workout.Status.COMPLETED
    base_data.workout.save()
    row = base_data.workout.workout_exercises.first()
    data = payload(base_data)
    data.update(
        {
            "items-INITIAL_FORMS": "1",
            "items-0-id": str(row.pk),
            "items-0-weight": "55",
            "status": "active",
        }
    )
    before = Workout.objects.count()
    response = browser().post("/workouts/1/edit/", data)
    assert response.status_code == 302
    assert Workout.objects.count() == before
    row.refresh_from_db()
    base_data.workout.refresh_from_db()
    assert row.weight == 55
    assert base_data.workout.status == Workout.Status.COMPLETED


def test_cannot_delete_all_rows(base_data):
    rows = list(base_data.workout.workout_exercises.all())
    data = payload(base_data, len(rows))
    data["items-INITIAL_FORMS"] = str(len(rows))
    for i, row in enumerate(rows):
        data[f"items-{i}-id"] = str(row.pk)
        data[f"items-{i}-DELETE"] = "on"
    response = browser().post("/workouts/1/edit/", data)
    assert response.status_code == 200
    assert response.context["formset"].non_form_errors()
    assert base_data.workout.workout_exercises.count() == len(rows)


def test_atomic_rollback_if_row_save_fails(base_data, monkeypatch):
    before = Workout.objects.count()

    def fail(*args, **kwargs):
        raise IntegrityError("simulated row failure")

    monkeypatch.setattr(WorkoutExercise, "save", fail)
    with pytest.raises(IntegrityError):
        browser().post("/workouts/create/", payload(base_data))
    assert Workout.objects.count() == before


def test_cancel_post_only_and_preserves_history(base_data):
    client = browser()
    assert client.get("/workouts/1/cancel/").status_code == 405
    assert client.post("/workouts/1/cancel/").status_code == 302
    base_data.workout.refresh_from_db()
    assert base_data.workout.status == Workout.Status.CANCELLED
    assert base_data.workout.workout_exercises.count() == 3
    assert client.post("/workouts/1/cancel/").status_code == 302
    assert Workout.objects.count() == 1


def test_completed_is_not_cancelled_by_user_endpoint(base_data):
    base_data.workout.status = Workout.Status.COMPLETED
    base_data.workout.save()
    browser().post("/workouts/1/cancel/")
    base_data.workout.refresh_from_db()
    assert base_data.workout.status == Workout.Status.COMPLETED


@pytest.mark.parametrize("url", ["/workouts/999/edit/", "/exercises/999/edit/"])
def test_missing_edit_object_is_404(url):
    assert browser().get(url).status_code == 404


@pytest.mark.parametrize(
    "url",
    [
        "/workouts/create/",
        "/workouts/1/edit/",
        "/workouts/1/cancel/",
        "/exercises/create/",
        "/exercises/1/edit/",
    ],
)
def test_csrf_rejects_post_without_token(base_data, url):
    assert browser(csrf=True).post(url, {}).status_code == 403


def test_real_csrf_form_token_allows_create_and_cancel(base_data):
    client = browser(csrf=True)
    client.get("/workouts/create/")
    data = payload(base_data)
    data["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
    response = client.post("/workouts/create/", data)
    assert response.status_code == 302
    pk = Workout.objects.latest("pk").pk
    assert (
        client.post(
            f"/workouts/{pk}/cancel/",
            {
                "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            },
        ).status_code
        == 302
    )


def image_upload(name="photo.png", fmt="PNG"):
    stream = BytesIO()
    Image.new("RGB", (8, 8), "blue").save(stream, format=fmt)
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


def test_image_create_edit_display_and_clear(base_data, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client = browser()
    response = client.post(
        "/exercises/create/",
        {
            "name": "Новое упражнение",
            "muscle_group": "Ноги",
            "image": image_upload(),
        },
    )
    assert response.status_code == 302
    obj = Exercise.objects.latest("pk")
    assert Path(obj.image.path).is_file()
    assert obj.image.url in client.get(obj.get_absolute_url()).content.decode()
    first_name = obj.image.name
    response = client.post(
        f"/exercises/{obj.pk}/edit/",
        {
            "name": obj.name,
            "muscle_group": obj.muscle_group,
            "image": image_upload("new.png"),
        },
    )
    assert response.status_code == 302
    obj.refresh_from_db()
    assert obj.image.name != first_name
    response = client.post(
        f"/exercises/{obj.pk}/edit/",
        {
            "name": obj.name,
            "muscle_group": obj.muscle_group,
            "image-clear": "on",
        },
    )
    assert response.status_code == 302
    obj.refresh_from_db()
    assert not obj.image


@pytest.mark.parametrize("content", [b"not an image", b"<svg>fake</svg>"])
def test_bad_image_rejected_without_saving(content, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    response = browser().post(
        "/exercises/create/",
        {
            "name": "Неверный файл",
            "muscle_group": "Ноги",
            "image": SimpleUploadedFile("fake.png", content, content_type="image/png"),
        },
    )
    assert response.status_code == 200
    assert "image" in response.context["form"].errors
    assert Exercise.objects.count() == 0
    assert not list(tmp_path.rglob("*"))


def test_image_size_validator():
    from exercises.forms import validate_image_size
    from django.core.exceptions import ValidationError

    image = SimpleUploadedFile("huge.png", b"0" * (5 * 1024 * 1024 + 1))
    with pytest.raises(ValidationError):
        validate_image_size(image)


def test_optional_image_and_model_fields():
    form = ExerciseForm({"name": "Без фото", "muscle_group": "Ноги"})
    assert form.is_valid()
    obj = form.save()
    assert not obj.image
    assert set(WorkoutForm().fields) == {
        "user",
        "workout_date",
        "workout_type",
        "duration_min",
    }


def test_invalid_edit_does_not_save_parent_or_rows(base_data):
    row = base_data.workout.workout_exercises.first()
    before = (base_data.workout.duration_min, row.weight)
    data = payload(base_data)
    data.update(
        {
            "duration_min": "15",
            "items-INITIAL_FORMS": "1",
            "items-0-id": str(row.pk),
            "items-0-weight": "-1",
        }
    )
    response = browser().post("/workouts/1/edit/", data)
    assert response.status_code == 200
    base_data.workout.refresh_from_db()
    row.refresh_from_db()
    assert (base_data.workout.duration_min, row.weight) == before


def test_image_preserved_when_editing_without_new_upload(base_data, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    obj = base_data.bench
    obj.image.save("original.png", image_upload(), save=True)
    old_name = obj.image.name
    response = browser().post(
        f"/exercises/{obj.pk}/edit/",
        {
            "name": "Изменённое название",
            "muscle_group": obj.muscle_group,
        },
    )
    assert response.status_code == 302
    obj.refresh_from_db()
    assert obj.name == "Изменённое название"
    assert obj.image.name == old_name


def test_admin_upload_and_replace_image(base_data, settings, tmp_path):
    from django.contrib.auth import get_user_model

    settings.MEDIA_ROOT = tmp_path
    client = browser()
    admin = get_user_model().objects.create_superuser(
        "image-admin", password="test-only"
    )
    client.force_login(admin)
    obj = base_data.bench
    url = reverse("admin:exercises_exercise_change", args=[obj.pk])
    data = {
        "name": obj.name,
        "muscle_group": obj.muscle_group,
        "slug": obj.slug,
        "workout_exercises-TOTAL_FORMS": "0",
        "workout_exercises-INITIAL_FORMS": "0",
        "workout_exercises-MIN_NUM_FORMS": "0",
        "workout_exercises-MAX_NUM_FORMS": "1000",
        "_save": "Сохранить",
    }
    response = client.post(url, {**data, "image": image_upload("admin.png")})
    assert response.status_code == 302
    obj.refresh_from_db()
    old = obj.image.name
    assert Path(obj.image.path).is_file()
    response = client.post(url, {**data, "image": image_upload("replacement.png")})
    assert response.status_code == 302
    obj.refresh_from_db()
    assert obj.image.name != old
    assert obj.image.url in browser().get(obj.get_absolute_url()).content.decode()
