from django.contrib import admin
from workouts.models import Workout
from .models import User


class WorkoutInline(admin.TabularInline):
    model = Workout
    fields = ("workout_date", "workout_type", "duration_min", "status")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "registered_at")
    list_display_links = ("id", "name")
    search_fields = ("name",)
    list_filter = ("registered_at",)
    ordering = ("name", "pk")
    readonly_fields = ("id",)
    list_per_page = 20
    inlines = (WorkoutInline,)
