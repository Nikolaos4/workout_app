from django.db import models


class WorkoutQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status="active")

    def cancelled(self):
        return self.filter(status="cancelled")

    def for_date(self, selected_date):
        return self.filter(workout_date=selected_date)

    def with_user(self):
        return self.select_related("user")

    def completed(self):
        return self.filter(status=self.model.Status.COMPLETED)

    def counted(self):
        """Тренировки, учитываемые в нагрузке: активные и завершённые."""
        return self.exclude(status=self.model.Status.CANCELLED)
