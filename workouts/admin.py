"""Админ-зона: тренировки со строками выполненных упражнений."""

from django.contrib import admin

from .models import Workout, WorkoutExercise


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 1


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = (
        "workout_date",
        "user",
        "workout_type",
        "duration_min",
        "is_cancelled",
    )
    list_filter = ("workout_type", "is_cancelled")
    search_fields = ("user__name",)
    inlines = [WorkoutExerciseInline]
