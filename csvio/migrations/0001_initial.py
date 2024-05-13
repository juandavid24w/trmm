# Generated by Django 5.0.4 on 2024-05-16 03:17

import csvio.models
import csvio.registry
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CSVExport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        default=csvio.models.export_name,
                        max_length=127,
                        verbose_name="Nome",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de criação"
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        editable=False,
                        upload_to="csvio/exports/",
                        verbose_name="Arquivo de exportação",
                    ),
                ),
                (
                    "key",
                    models.CharField(
                        choices=csvio.registry.CSVIORegistry.get_model_export_choices,
                        default="books.book",
                        max_length=127,
                        verbose_name="Tipo de dado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Exportação CSV",
                "verbose_name_plural": "Exportações CSV",
            },
        ),
        migrations.CreateModel(
            name="CSVImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        default=csvio.models.import_name,
                        max_length=127,
                        verbose_name="Nome",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de criação"
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to="csvio/imports/", verbose_name="Arquivo de importação"
                    ),
                ),
                (
                    "error_file",
                    models.FileField(
                        editable=False,
                        null=True,
                        upload_to="csvio/imports/errors/",
                        verbose_name="Arquivo com erros",
                    ),
                ),
                (
                    "key",
                    models.CharField(
                        choices=csvio.registry.CSVIORegistry.get_model_import_choices,
                        default="books.book",
                        max_length=127,
                        verbose_name="Tipo de dado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Importação CSV",
                "verbose_name_plural": "Importações CSV",
            },
        ),
    ]
