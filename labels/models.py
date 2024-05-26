import re
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from fpdf.fpdf import PAGE_FORMATS
from isbnlib import mask

from books.models import Specimen
from default_object.models import DefaultObjectMixin


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

class LabelPageConfiguration(DefaultObjectMixin, models.Model):
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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Configuração de página")
        verbose_name_plural = _("Configurações de página")


class LabelPrint(models.Model):
    class BarcodeChoices(models.IntegerChoices):
        NO_BARCODE = 1, _("Não incluir código de barras")
        USE_ISBN = 2, _(
            "Incluir código de barras do ISBN (se não houver, usa o "
            "identificador)"
        )
        USE_ID = 3, _("Incluir código de barras do identificador")
        ONLY_NO_ISBN = 4, _(
            "Só incluir código de barras se o exemplar não tiver ISBN"
        )
        ONLY_WITH_ISBN = 5, _("Só incluir código de barras do ISBN")

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
    use_color = models.BooleanField(verbose_name=_("Usar cor"), default=False)
    use_border = models.BooleanField(
        verbose_name=_("Usar borda"), default=False
    )
    include_title = models.BooleanField(
        verbose_name=_("incluir título"), default=False
    )
    barcode_option = models.IntegerField(
        verbose_name=_("Opções de código de barra"),
        choices=BarcodeChoices,
        default=BarcodeChoices.NO_BARCODE,
    )
    include_marked = models.BooleanField(
        verbose_name=_(
            "Incluir exemplares com marcação de etiqueta impressa"
        ),
        default=False,
    )
    mark_labeled = models.BooleanField(
        verbose_name=_("Fazer marcação de etiqueta impressa nos exemplares"),
        default=True,
    )
    status = models.CharField(
        verbose_name=_("Status do processamento"),
        max_length=512,
        default="",
        blank=True,
        editable=False,
    )
    labels_file = models.FileField(
        verbose_name=_("Arquivo com as etiquetas"),
        upload_to="labels",
    )

    def resolve_barcode(self, conf, specimen):
        no = (False, None, None)
        isbn = (
            True,
            specimen.book.canonical_isbn,
            mask(specimen.book.canonical_isbn),
        )
        id_ = (True, specimen.id, str(specimen.id))

        match conf.barcode_option:
            case self.BarcodeChoices.NO_BARCODE:
                return False, None, None
            case self.BarcodeChoices.USE_ID:
                return id_
            case self.BarcodeChoices.USE_ISBN:
                if specimen.book.canonical_isbn:
                    return isbn
                return id_
            case self.BarcodeChoices.ONLY_NO_ISBN:
                if specimen.book.canonical_isbn:
                    return no
                return id_
            case self.BarcodeChoices.ONLY_WITH_ISBN:
                if specimen.book.canonical_isbn:
                    return isbn
                return no
            case _:
                raise ValueError("Expected BarcodeChoice value")

    def n_labels(self):
        return self.specimens.count()

    def save(self, *args, **kwargs):
        if not self.status:
            self.status = gettext("Processamento não iniciado.")
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
