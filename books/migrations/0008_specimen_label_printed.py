# Generated by Django 5.0.4 on 2024-05-23 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0007_collection_unique_collection_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="specimen",
            name="label_printed",
            field=models.BooleanField(default=False, verbose_name="Etiqueta impressa?"),
        ),
    ]