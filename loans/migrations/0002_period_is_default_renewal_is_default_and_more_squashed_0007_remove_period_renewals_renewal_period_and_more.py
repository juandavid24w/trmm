# Generated by Django 5.0.4 on 2024-05-20 01:24

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("loans", "0002_period_is_default_renewal_is_default_and_more"),
        ("loans", "0003_alter_period_options_remove_loan_duration_and_more"),
        ("loans", "0004_alter_renewal_description"),
        ("loans", "0005_remove_renewal_is_default"),
        ("loans", "0006_alter_period_description_alter_renewal_description"),
        ("loans", "0007_remove_period_renewals_renewal_period_and_more"),
    ]

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("books", "0004_collection_book_collection"),
        ("loans", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="period",
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
            field=models.CharField(
                blank=True, max_length=128, verbose_name="Descrição"
            ),
        ),
        migrations.AlterModelOptions(
            name="period",
            options={
                "ordering": ["order"],
                "verbose_name": "Período",
                "verbose_name_plural": "Períodos",
            },
        ),
        migrations.RenameField(
            model_name="loan",
            old_name="duration",
            new_name="period",
        ),
        migrations.AlterField(
            model_name="loan",
            name="period",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.RESTRICT,
                to="loans.period",
                verbose_name="Duração",
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="books",
            field=models.ManyToManyField(
                blank=True, to="books.book", verbose_name="Livros"
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="classifications",
            field=models.ManyToManyField(
                blank=True, to="books.classification", verbose_name="Classificações"
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="collections",
            field=models.ManyToManyField(
                blank=True, to="books.collection", verbose_name="Acervos"
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="groups",
            field=models.ManyToManyField(
                blank=True, to="auth.group", verbose_name="Grupos"
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="locations",
            field=models.ManyToManyField(
                blank=True, to="books.location", verbose_name="Localizações"
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="logical_operator",
            field=models.IntegerField(
                blank=True,
                choices=[(1, "ou"), (2, "e")],
                default=1,
                help_text="Indica se vale esse período quando qualquer uma das condições abaixo for respeitada ('ou'), ou se vale esse periodo quando todas elas forem respeitadas ('e')",
                verbose_name="Operador lógico",
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="order",
            field=models.PositiveIntegerField(default=0, verbose_name="Ordem"),
        ),
        migrations.AddField(
            model_name="period",
            name="specimens",
            field=models.ManyToManyField(
                blank=True, to="books.specimen", verbose_name="Exemplares"
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="users",
            field=models.ManyToManyField(
                blank=True, to=settings.AUTH_USER_MODEL, verbose_name="Usuários"
            ),
        ),
        migrations.AlterField(
            model_name="loan",
            name="renewals",
            field=models.ManyToManyField(
                blank=True,
                editable=False,
                to="loans.renewal",
                verbose_name="Renovações",
            ),
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
            field=models.TextField(default="Período normal", verbose_name="Descrição"),
        ),
        migrations.AddField(
            model_name="renewal",
            name="period",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="renewals",
                to="loans.period",
                verbose_name="Período",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="loan",
            name="date",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="Data do empréstimo"
            ),
        ),
    ]
