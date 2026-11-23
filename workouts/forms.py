"""Фильтры и формы тренировок с сохранением правил предметной области."""

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone

from users.models import User
from .models import Workout, WorkoutExercise

SORT_CHOICES = (
    ("date", "дате (сначала новые)"),
    ("date_asc", "дате (сначала старые)"),
    ("user", "пользователю"),
    ("duration", "длительности"),
    ("tonnage", "тоннажу"),
)


def style_fields(form):
    """Одинаковое Bootstrap-оформление без стороннего пакета форм."""
    for field in form.fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(field.widget, forms.Select):
            css = "form-select"
        else:
            css = "form-control"
        field.widget.attrs["class"] = css


class WorkoutFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=200,
        label="Поиск",
        widget=forms.TextInput(attrs={"placeholder": "имя или тип"}),
    )
    user = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=999999999,
        label="Пользователь",
        widget=forms.Select,
    )
    type = forms.ChoiceField(
        required=False,
        label="Тип",
        choices=(("", "— любой —"), *Workout.WorkoutType.choices),
    )
    start = forms.DateField(
        required=False,
        label="С даты",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    end = forms.DateField(
        required=False,
        label="По дату",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    sort = forms.ChoiceField(
        required=False, choices=SORT_CHOICES, initial="date", label="Сортировать по"
    )
    active = forms.BooleanField(
        required=False,
        label="Только активные",
        widget=forms.CheckboxInput(attrs={"value": "1"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].widget.choices = [
            ("", "— все —"),
            *((user.pk, user.name) for user in User.objects.order_by("name")),
        ]
        style_fields(self)

    def clean_active(self):
        return self.data.get("active") == "1"

    def clean(self):
        data = super().clean()
        start, end = data.get("start"), data.get("end")
        if start and end and start > end:
            raise ValidationError("Начало периода не может быть позже конца.")
        return data


class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        # Статус и идентификатор не принимаем из пользовательского POST.
        fields = ("user", "workout_date", "workout_type", "duration_min")
        labels = {"user": "Пользователь", "workout_date": "Дата тренировки"}
        help_texts = {
            "workout_date": "Укажите дату выполненной тренировки, не позднее сегодня.",
            "duration_min": "Длительность в минутах, не меньше нуля.",
        }
        widgets = {
            "workout_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "duration_min": forms.NumberInput(attrs={"min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["workout_date"].initial = timezone.localdate
        style_fields(self)

    def clean_workout_date(self):
        value = self.cleaned_data["workout_date"]
        if value > timezone.localdate():
            raise ValidationError("Дата тренировки не может быть в будущем.")
        return value


class WorkoutExerciseForm(forms.ModelForm):
    class Meta:
        model = WorkoutExercise
        fields = ("exercise", "sets", "reps", "weight")
        help_texts = {"weight": "Вес в килограммах. Для упражнений без веса укажите 0."}
        widgets = {
            "sets": forms.NumberInput(attrs={"min": 0}),
            "reps": forms.NumberInput(attrs={"min": 0}),
            "weight": forms.NumberInput(attrs={"min": 0, "step": "any"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class RequiredExercisesFormSet(BaseInlineFormSet):
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


WorkoutExerciseFormSet = inlineformset_factory(
    Workout,
    WorkoutExercise,
    form=WorkoutExerciseForm,
    formset=RequiredExercisesFormSet,
    extra=1,
    can_delete=True,
    max_num=30,
    validate_max=True,
    absolute_max=60,
)
