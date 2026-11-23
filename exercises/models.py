"""Модель справочника упражнений."""

from django.db import models


class Exercise(models.Model):
    """Упражнение: название и рабочая группа мышц."""

    name = models.CharField(
        max_length=200,
        verbose_name="Название упражнения",
    )
    muscle_group = models.CharField(
        max_length=100,
        verbose_name="Группа мышц",
    )

    slug = models.SlugField(
        max_length=220, unique=True, blank=True, verbose_name="Адрес на английском"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            import uuid
            from django.utils.text import slugify

            base = slugify(self.name) or "exercise"
            self.slug = f"{base[:180]}-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("exercises:detail_slug", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"
