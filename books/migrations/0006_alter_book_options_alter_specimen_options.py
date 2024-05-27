# Generated by Django 5.0.4 on 2024-05-22 20:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0005_alter_collection_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="book",
            options={
                "ordering": ["author_last_name", "title"],
                "verbose_name": "Livro",
                "verbose_name_plural": "Livros",
            },
        ),
        migrations.AlterModelOptions(
            name="specimen",
            options={
                "ordering": ["book__author_last_name", "book__title", "number"],
                "verbose_name": "Exemplar",
                "verbose_name_plural": "Exemplares",
            },
        ),
    ]