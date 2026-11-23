from django.db import migrations, models


def populate_slugs(apps, schema_editor):
    Exercise = apps.get_model("exercises", "Exercise")
    for obj in Exercise.objects.all().iterator():
        obj.slug = f"exercise-{obj.pk}"
        obj.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [("exercises", "0001_initial")]
    operations = [
        migrations.AddField(model_name="exercise", name="slug",
            field=models.SlugField(max_length=220, null=True, blank=True,
                                   verbose_name="Адрес на английском")),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(model_name="exercise", name="slug",
            field=models.SlugField(max_length=220, unique=True, blank=True,
                                   verbose_name="Адрес на английском")),
    ]
