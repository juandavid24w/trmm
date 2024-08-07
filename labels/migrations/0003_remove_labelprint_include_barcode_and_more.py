# Generated by Django 5.0.4 on 2024-05-23 00:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("labels", "0002_labelpageconfiguration_is_default"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="labelprint",
            name="include_barcode",
        ),
        migrations.RemoveField(
            model_name="labelprint",
            name="use_isbn",
        ),
        migrations.AddField(
            model_name="labelprint",
            name="barcode_option",
            field=models.IntegerField(
                choices=[
                    (1, "Não incluir código de barras"),
                    (
                        2,
                        "Incluir código de barras do ISBN (se não houver, usa o identificador)",
                    ),
                    (3, "Incluir código de barras do identificador"),
                    (4, "Só incluir código de barras se o exemplar não tiver ISBN"),
                    (5, "Só incluir código de barras do ISBN"),
                ],
                default=1,
                verbose_name="Opções de código de barra",
            ),
        ),
        migrations.AddField(
            model_name="labelprint",
            name="include_title",
            field=models.BooleanField(default=False, verbose_name="incluir título"),
        ),
        migrations.AlterField(
            model_name="labelprint",
            name="labels_file",
            field=models.FileField(
                help_text="Salve para gerar esse arquivo novamente",
                upload_to="labels",
                verbose_name="Arquivo com as etiquetas",
            ),
        ),
    ]
