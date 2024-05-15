# Generated by Django 5.0.4 on 2024-05-15 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("books", "0005_alter_book_author_first_names"),
        ("books", "0006_alter_classification_options_alter_location_options"),
    ]

    dependencies = [
        ("books", "0004_alter_book_code_alter_book_publisher"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="author_first_names",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="Primeiros nomes do autor",
            ),
        ),
        migrations.AlterModelOptions(
            name="classification",
            options={
                "ordering": ["abbreviation"],
                "verbose_name": "Classificação",
                "verbose_name_plural": "Classificações",
            },
        ),
        migrations.AlterModelOptions(
            name="location",
            options={
                "ordering": ["name"],
                "verbose_name": "Localização",
                "verbose_name_plural": "Localizações",
            },
        ),
    ]
