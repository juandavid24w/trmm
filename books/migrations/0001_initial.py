# Generated by Django 5.0.4 on 2024-05-05 04:59

import books.validators
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Classification",
            fields=[
                (
                    "abbreviation",
                    models.CharField(
                        max_length=20,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Abreviação",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=80, verbose_name="Nome"),
                ),
            ],
            options={
                "verbose_name": "Classificação",
                "verbose_name_plural": "Classificações",
            },
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "name",
                    models.CharField(
                        max_length=20,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Nome",
                    ),
                ),
            ],
            options={
                "verbose_name": "Localização",
                "verbose_name_plural": "Localizações",
            },
        ),
        migrations.CreateModel(
            name="Book",
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
                    "isbn",
                    models.CharField(
                        max_length=13,
                        null=True,
                        validators=[books.validators.validate_isbn],
                        verbose_name="ISBN",
                    ),
                ),
                ("title", models.TextField(verbose_name="Título")),
                (
                    "author_first_names",
                    models.CharField(
                        max_length=100, verbose_name="Primeiros nomes do autor"
                    ),
                ),
                (
                    "author_last_name",
                    models.CharField(
                        max_length=50, verbose_name="Último nome do autor"
                    ),
                ),
                ("publisher", models.CharField(max_length=300, verbose_name="Editora")),
                (
                    "title_first_letter",
                    models.CharField(
                        help_text="Primeira letra da primeira palavra do título que não é um artigo",
                        max_length=1,
                        verbose_name="Primeira letra do título",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Código do livro sem o número de exemplar",
                        max_length=50,
                        null=True,
                        verbose_name="Código parcial do livro",
                    ),
                ),
                (
                    "creation_date",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de criação"
                    ),
                ),
                (
                    "last_modified",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Última modificação"
                    ),
                ),
                (
                    "classification",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="books.classification",
                        verbose_name="Classificação",
                    ),
                ),
            ],
            options={
                "verbose_name": "Livro",
                "verbose_name_plural": "Livros",
            },
        ),
        migrations.AddField(
            model_name="classification",
            name="location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="books.location",
                verbose_name="Localização",
            ),
        ),
        migrations.CreateModel(
            name="Specimen",
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
                    "number",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Número",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        blank=True, default="", max_length=50, verbose_name="Código"
                    ),
                ),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="specimens",
                        to="books.book",
                        verbose_name="Livro",
                    ),
                ),
            ],
            options={
                "verbose_name": "Exemplar",
                "verbose_name_plural": "Exemplares",
            },
        ),
        migrations.AddConstraint(
            model_name="book",
            constraint=models.UniqueConstraint(
                fields=("isbn",), name="unique isbn"
            ),
        ),
        migrations.AddConstraint(
            model_name="specimen",
            constraint=models.UniqueConstraint(
                fields=("number", "book"), name="unique specimen number"
            ),
        ),
    ]
