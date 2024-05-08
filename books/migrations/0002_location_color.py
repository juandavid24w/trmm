# Generated by Django 5.0.4 on 2024-05-06 13:53

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="color",
            field=colorfield.fields.ColorField(
                blank=True,
                default=None,
                image_field=None,
                max_length=25,
                null=True,
                samples=None,
                verbose_name="Cor",
            ),
        ),
    ]