"""Создание и редактирование упражнений с необязательным изображением."""

from django import forms
from django.core.exceptions import ValidationError

from workouts.forms import style_fields
from .models import Exercise


def validate_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Размер изображения не должен превышать 5 МБ.")


class ExerciseForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        label="Изображение",
        validators=[validate_image_size],
        help_text="JPEG, PNG или WebP, до 5 МБ.",
    )

    class Meta:
        model = Exercise
        fields = ("name", "muscle_group", "image")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Например, жим лёжа"}),
            "muscle_group": forms.TextInput(attrs={"placeholder": "Например, грудь"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "image"):
            if image.image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValidationError("Выберите изображение JPEG, PNG или WebP.")
        return image
