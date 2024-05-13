import re
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode

from .io import csv_export
from .registry import CSVIORegistry


def import_name():
    return _("%(date)s - importação") % {
        "date": timezone.now().strftime("%y.%m.%d")
    }


def export_name():
    return _("%(date)s - exportação") % {
        "date": timezone.now().strftime("%y.%m.%d")
    }

class CSVImport(models.Model):
    name = models.CharField(
        max_length=127,
        verbose_name=_("Nome"),
        default=import_name,
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de criação"),
    )
    file = models.FileField(
        verbose_name=_("Arquivo de importação"), upload_to="csvio/imports/"
    )
    error_file = models.FileField(
        verbose_name=_("Arquivo com erros"),
        editable=False,
        null=True,
        upload_to="csvio/imports/errors/",
    )
    key = models.CharField(
        max_length=127,
        verbose_name=_("Tipo de dado"),
        choices=CSVIORegistry.get_model_import_choices,
        default=getattr(settings, "CSVIO_DEFAULT_MODEL", None),
    )

    def get_model(self):
        return apps.get_model(".".join(self.key.split(".")[:2]))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Importação CSV")
        verbose_name_plural = _("Importações CSV")


class CSVExport(models.Model):
    name = models.CharField(
        max_length=127,
        verbose_name=_("Nome"),
        default=export_name,
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de criação"),
    )
    file = models.FileField(
        verbose_name=_("Arquivo de exportação"),
        editable=False,
        upload_to="csvio/exports/",
    )
    key = models.CharField(
        max_length=127,
        verbose_name=_("Tipo de dado"),
        choices=CSVIORegistry.get_model_export_choices,
        default=getattr(settings, "CSVIO_DEFAULT_MODEL", None),
    )

    def rename_file(self):
        mo = re.search(r"_(\w+\.\w+.\w+).csv$", self.file.path)
        model_part = mo.group(1)
        if model_part != self.key:
            path = Path(self.file.path)
            path.rename(path.parent / path.name.replace(model_part, self.key))
            self.file.name = self.file.name.replace(model_part, self.key)

    def save(self, *args, **kwargs):
        if self.key:
            content = csv_export(self.key)
            if self.file and self.file.path:
                with open(self.file.path, "wb") as f:
                    f.write(content)
                self.rename_file()
            else:
                self.file.save(
                    name=(
                        unidecode(self.name.replace(" - ", "_"))
                        or gettext("exportacao")
                    )
                    + f"_{self.key}.csv",
                    content=ContentFile(content),
                    save=False,
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Exportação CSV")
        verbose_name_plural = _("Exportações CSV")


@receiver(pre_delete, sender=CSVExport)
def delete_export_files_hook(sender, instance, *args, **kwargs):
    try:
        (settings.MEDIA_ROOT / instance.file.name).unlink()
    except OSError:
        pass


@receiver(pre_delete, sender=CSVImport)
def delete_import_files_hook(sender, instance, *args, **kwargs):
    try:
        (settings.MEDIA_ROOT / instance.file.name).unlink()
    except OSError:
        pass
    try:
        (settings.MEDIA_ROOT / instance.error_file.name).unlink()
    except OSError:
        pass
