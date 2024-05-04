# Generated by Django 5.0.4 on 2024-05-04 23:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Email",
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
                ("email", models.EmailField(max_length=254)),
                (
                    "receive_notifications",
                    models.BooleanField(
                        default=True, verbose_name="Receber notificações"
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="additional_emails",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Email adicional",
                "verbose_name_plural": "Emails adicionais",
            },
        ),
        migrations.CreateModel(
            name="Profile",
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
                    "grade",
                    models.CharField(
                        choices=[
                            (None, None),
                            ("6EF", "6º ano do ensino fundamental"),
                            ("7EF", "7º ano do ensino fundamental"),
                            ("8EF", "8º ano do ensino fundamental"),
                            ("9EF", "9º ano do ensino fundamental"),
                            ("1EM", "1ª série do ensino médio"),
                            ("2EM", "2ª série do ensino médio"),
                            ("3EM", "3ª série do ensino médio"),
                        ],
                        default=None,
                        max_length=3,
                        null=True,
                        verbose_name="Série",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Perfil",
                "verbose_name_plural": "Perfis",
            },
        ),
    ]
