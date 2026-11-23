"""Административная панель тренировок и выполненных упражнений."""

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import Workout, WorkoutExercise


class WorkoutExerciseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if not any(
            form.cleaned_data and not form.cleaned_data.get("DELETE", False)
            for form in self.forms
        ):
            raise ValidationError(
                "Тренировка должна содержать хотя бы одно упражнение."
            )


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    formset = WorkoutExerciseFormSet
    extra = 0
    min_num = 1
    autocomplete_fields = ("exercise",)


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "workout_date",
        "user",
        "workout_type",
        "duration_min",
        "status",
    )
    list_display_links = ("id", "workout_date")
    list_filter = ("workout_type", "status", "workout_date", "user")
    search_fields = ("user__name", "workout_type")
    ordering = ("-workout_date", "-pk")
    list_per_page = 20
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    readonly_fields = ("id",)
    date_hierarchy = "workout_date"
    inlines = (WorkoutExerciseInline,)
    actions = ("cancel_workouts",)

    @admin.action(description="Отменить выбранные тренировки")
    def cancel_workouts(self, request, queryset):
        count = queryset.active().update(status="cancelled")
        self.message_user(request, f"Отменено тренировок: {count}")
