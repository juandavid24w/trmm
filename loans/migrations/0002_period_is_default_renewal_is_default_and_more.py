# Generated by Django 5.0.4 on 2024-05-16 16:13

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("loans", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="period",
            name="is_default",
            field=models.BooleanField(default=False, verbose_name="É o padrão?"),
        ),
        migrations.AddField(
            model_name="renewal",
            name="is_default",
            field=models.BooleanField(default=False, verbose_name="É o padrão?"),
        ),
        migrations.AlterField(
            model_name="period",
            name="days",
            field=models.IntegerField(
                default=15,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Número de dias",
            ),
        ),
        migrations.AlterField(
            model_name="period",
            name="description",
            field=models.TextField(
                blank=True, default="Empréstimo normal", verbose_name="Descrição"
            ),
        ),
        migrations.AlterField(
            model_name="renewal",
            name="days",
            field=models.IntegerField(
                default=15,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Número de dias",
            ),
        ),
        migrations.AlterField(
            model_name="renewal",
            name="description",
            field=models.TextField(
                blank=True, default="Primeira renovação", verbose_name="Descrição"
            ),
        ),
    ]