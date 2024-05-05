# Generated by Django 5.0.4 on 2024-05-05 18:03

import django.db.models.deletion
import tinymce.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("loans", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
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
                ("name", models.CharField(max_length=100, verbose_name="Nome")),
                ("subject", models.CharField(max_length=100, verbose_name="Assunto")),
                (
                    "message",
                    tinymce.models.HTMLField(
                        help_text="Variáveis disponíveis: {{ name }}, {{ signature }}{{ site_title }}, {{ due }} e {{ book }}{{ late_days }}",
                        verbose_name="Mensagem",
                    ),
                ),
                (
                    "n_parameter",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Parâmetro <n>"
                    ),
                ),
            ],
            options={
                "verbose_name": "Notificação",
                "verbose_name_plural": "Notificações",
            },
        ),
        migrations.CreateModel(
            name="Trigger",
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
                    "ttype",
                    models.IntegerField(
                        choices=[
                            (1, "Expira em <n> dias"),
                            (2, "Atrasado há <n> dias"),
                            (3, "Atrasado a cada <n> dias"),
                        ],
                        verbose_name="tipo de gatilho",
                    ),
                ),
            ],
            options={
                "verbose_name": "Gatilho",
                "verbose_name_plural": "Gatilhos",
            },
        ),
        migrations.CreateModel(
            name="NotificationLog",
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
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="Data"),
                ),
                (
                    "loan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="loans.loan",
                        verbose_name="Empréstimo",
                    ),
                ),
                (
                    "notification",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="notifications.notification",
                        verbose_name="Notificação",
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de notificação",
                "verbose_name_plural": "Registros de notificação",
            },
        ),
        migrations.AddConstraint(
            model_name="trigger",
            constraint=models.UniqueConstraint(fields=("ttype",), name="unique ttype"),
        ),
        migrations.AddField(
            model_name="notification",
            name="triggers",
            field=models.ManyToManyField(to="notifications.trigger"),
        ),
    ]
