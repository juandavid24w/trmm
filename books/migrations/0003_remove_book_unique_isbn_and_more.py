# Generated by Django 5.0.4 on 2024-05-12 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0002_location_color"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="book",
            name="unique isbn",
        ),
        migrations.RemoveField(
            model_name="book",
            name="title_first_letter",
        ),
        migrations.RemoveField(
            model_name="specimen",
            name="code",
        ),
        migrations.AlterField(
            model_name="book",
            name="code",
            field=models.CharField(
                default="", max_length=50, verbose_name="Código cutter"
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="book",
            constraint=models.UniqueConstraint(fields=("isbn",), name="unique_isbn"),
        ),
        migrations.AddConstraint(
            model_name="book",
            constraint=models.UniqueConstraint(fields=("code",), name="unique_code"),
        ),
    ]
