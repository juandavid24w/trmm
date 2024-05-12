import re
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from fpdf.fpdf import PAGE_FORMATS

from books.models import Specimen

from .labels import create, create_file


@dataclass
class Dimension:
    width: int
    height: int


def validate_page_size(value):
    if value.lower() not in PAGE_FORMATS and not re.match(r"\d+,\d+", value):
        raise ValidationError(
            "Tamanho da página deve ser a4, a3, a5, letter, legal "
            "ou dois números separados por vírgula"
        )


def label_name():
    return _("%(date)s - etiquetas") % {
        "date": timezone.now().strftime("%y.%m.%d")
    }

class LabelPageConfiguration(models.Model):
    name = models.CharField(
        max_length=127,
        verbose_name=_("Nome"),
        null=True,
        blank=True,
    )
    paper_size = models.CharField(
        max_length=10,
        verbose_name=_("Tamanho da página"),
        help_text=_(
            "Use dois números separados por vírgula, representando a "
            "largura e altura em milímetros, ou um dos seguintes: a4, "
            "a3, a5, letter ou legal"
        ),
        validators=[validate_page_size],
        default="a4",
    )
    n_rows = models.IntegerField(
        verbose_name=_("Número de linhas"), default=11
    )
    n_cols = models.IntegerField(
        verbose_name=_("Número de colunas"), default=3
    )
    margin_top = models.FloatField(
        verbose_name=_("Margem superior"), default=8
    )
    margin_bottom = models.FloatField(
        verbose_name=_("Margem inferior"), default=8.5
    )
    margin_left = models.FloatField(
        verbose_name=_("Marge esquerda"), default=6.5
    )
    margin_right = models.FloatField(
        verbose_name=_("Margem direita"), default=6.5
    )
    horizontal_gap = models.FloatField(
        verbose_name=_("Separação horizontal"), default=2.5
    )
    vertical_gap = models.FloatField(
        verbose_name=_("Separação vertical"), default=0
    )
    font_size = models.FloatField(
        verbose_name=_("Tamanho da fonte de informações"), default=8
    )

    @classmethod
    def get_default(cls):
        return cls.objects.first()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Configuração de página")
        verbose_name_plural = _("Configurações de página")


class LabelPrint(models.Model):
    name = models.CharField(
        max_length=127,
        verbose_name=_("Nome"),
        default=label_name,
    )
    configuration = models.ForeignKey(
        LabelPageConfiguration,
        on_delete=models.CASCADE,
        verbose_name=_("Configuração"),
    )
    specimens = models.ManyToManyField(
        Specimen,
        related_name="label_prints",
        verbose_name=_("Exemplares"),
        editable=False,
    )
    created = models.DateTimeField(
        auto_now_add="True", verbose_name=_("Data de criação")
    )
    labels_file = models.FileField(
        verbose_name=_("Arquivo com as etiquetas"),
        upload_to="labels",
    )
    use_color = models.BooleanField(verbose_name=_("Usar cor"), default=False)
    use_border = models.BooleanField(
        verbose_name=_("Usar borda"), default=False
    )
    include_barcode = models.BooleanField(
        verbose_name=_("Incluir código de barras"), default=False
    )
    use_isbn = models.BooleanField(
        default=False,
        verbose_name=_("Usar ISBN no código de barras"),
        help_text=_(
            "Caso contrário, usa o identificador único do exemplar. "
            "Só válido se o campo acima estiver ativado."
        ),
    )

    def save(self, *args, **kwargs):
        if self.id and self.specimens.count():
            if self.labels_file.name:
                create_file(self, self.labels_file.path)
            else:
                self.labels_file.save(
                    # Translators: Labels download filename
                    name=gettext("etiquetas") + ".pdf",
                    content=ContentFile(create(self)),
                    save=False,
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Arquivo de etiquetas")
        verbose_name_plural = _("Etiquetas")


@receiver(pre_delete, sender=LabelPrint)
def delete_files_hook(sender, instance, *args, **kwargs):
    try:
        (settings.MEDIA_ROOT / instance.labels_file.name).unlink()
    except OSError:
        pass
