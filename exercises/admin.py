from django.contrib import admin
from workouts.models import WorkoutExercise
from .models import Exercise


class ExerciseUsageInline(admin.TabularInline):
    model = WorkoutExercise
    fields = ("workout", "sets", "reps", "weight")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("workout__user")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "muscle_group")
    list_display_links = ("id", "name")
    list_editable = ("muscle_group",)
    list_filter = ("muscle_group",)
    search_fields = ("name", "muscle_group")
    ordering = ("name", "pk")
    readonly_fields = ("id",)
    list_per_page = 20
    inlines = (ExerciseUsageInline,)
