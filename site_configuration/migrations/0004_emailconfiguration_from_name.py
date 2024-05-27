# Generated by Django 5.0.4 on 2024-05-22 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("site_configuration", "0003_alter_emailconfiguration_signature"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailconfiguration",
            name="from_name",
            field=models.CharField(
                blank=True,
                default="Biblioteca",
                max_length=255,
                null=True,
                verbose_name="Nome do remetente",
            ),
        ),
    ]