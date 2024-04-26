from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext as _

from . import cutter
from .validators import validate_isbn


class Location(models.Model):
    name = models.CharField(
        primary_key=True, max_length=20, verbose_name=_("Nome")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Localização")
        verbose_name_plural = _("Localizações")


class Classification(models.Model):
    name = models.CharField(
        primary_key=True, max_length=20, verbose_name=_("Nome")
    )
    full_name = models.CharField(
        max_length=80, verbose_name=_("Nome por extenso"), blank=True
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, verbose_name=_("Localização")
    )

    def __str__(self):
        if self.full_name:
            return self.full_name
        return self.name

    class Meta:
        verbose_name = _("Classificação")
        verbose_name_plural = _("Classificações")


class Book(models.Model):
    isbn = models.CharField(
        max_length=13,
        validators=[validate_isbn],
        verbose_name=_("ISBN"),
        primary_key=True,
        null=False,
    )
    title = models.TextField(verbose_name=_("Título"))
    author_first_names = models.CharField(
        max_length=100, verbose_name=_("Primeiros nomes do autor")
    )
    author_last_name = models.CharField(
        max_length=50, verbose_name=_("Último nome do autor")
    )
    publisher = models.CharField(max_length=300, verbose_name=_("Editora"))
    classification = models.ForeignKey(
        Classification,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Classificação"),
    )
    code = models.CharField(max_length=20, verbose_name=_("Código"))

    def units(self):
        return self.specimens.count()

    def calc_code(self):
        return (
            f"{self.classification.name} {cutter.get(self.author_last_name)} "
            f"{self.classification.location}"
        )

    def author(self):
        return f"{self.author_first_names} {self.author_last_name}"

    def save(self, *args, **kwargs):
        self.code = self.calc_code()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = _("Livro")
        verbose_name_plural = _("Livros")


class Specimen(models.Model):
    number = models.IntegerField(
        verbose_name=_("Número"),
        null=False,
        validators=[MinValueValidator(1)],
    )
    book = models.ForeignKey(
        Book,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_("Livro"),
        related_name="specimens",
    )

    def __str__(self):
        return f"E{self.number} | {self.book}"

    def __init__(self, *args, **kwargs):
        cls = self.__class__
        if "number" not in kwargs and "book" in kwargs:
            kwargs["number"] = (
                cls.objects.filter(book=kwargs["book"]).count() + 1
            )

        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name = _("Exemplar")
        verbose_name_plural = _("Exemplares")
        constraints = [
            models.UniqueConstraint(
                fields=("number", "book"), name="unique specimen number"
            )
        ]
