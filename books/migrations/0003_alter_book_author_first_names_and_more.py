# Generated by Django 5.0.4 on 2024-05-16 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0002_alter_book_isbn"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="author_first_names",
            field=models.CharField(
                blank=True,
                max_length=1024,
                null=True,
                verbose_name="Primeiros nomes do autor",
            ),
        ),
        migrations.AlterField(
            model_name="book",
            name="author_last_name",
            field=models.CharField(max_length=255, verbose_name="Último nome do autor"),
        ),
        migrations.AlterField(
            model_name="book",
            name="publisher",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Editora"
            ),
        ),
        migrations.AlterField(
            model_name="book",
            name="unaccent_author",
            field=models.CharField(
                editable=False, max_length=255, verbose_name="Autor sem acento"
            ),
        ),
        migrations.AlterField(
            model_name="book",
            name="unaccent_title",
            field=models.TextField(editable=False, verbose_name="Título sem acentos"),
        ),
    ]
