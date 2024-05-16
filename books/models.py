from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, Q
from django.db.models.lookups import Exact
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from isbnlib import canonical, ean13
from unidecode import unidecode

from . import cutter
from .language import ARTICLES
from .validators import validate_isbn


class Location(models.Model):
    name = models.CharField(
        primary_key=True, max_length=20, verbose_name=_("Nome")
    )
    color = ColorField(
        null=True,
        blank=True,
        verbose_name=_("Cor"),
    )

    def __str__(self):
        return self.name

    def color_icon(self, size=16):
        if not self.color:
            return self.name
        return format_html(
            '<div style="display:flex;justify-content:center">'
            + '<svg width="{}" height="{}" xmlns="http://www.w3.org/2000/svg">'
            + '<circle cx="{}" cy="{}" r="{}" fill="{}" />'
            + "</svg>"
            + "</div>",
            size,
            size,
            f"{size / 2:.2f}",
            f"{size / 2:.2f}",
            f"{size / 2:.2f}",
            self.color,
        )

    class Meta:
        verbose_name = _("Localização")
        verbose_name_plural = _("Localizações")
        ordering = ["name"]


class Classification(models.Model):
    abbreviation = models.CharField(
        primary_key=True, max_length=20, verbose_name=_("Abreviação")
    )
    name = models.CharField(max_length=80, verbose_name=_("Nome"), blank=True)
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, verbose_name=_("Localização")
    )

    def __str__(self):
        if self.name:
            return self.name
        return self.abbreviation

    class Meta:
        verbose_name = _("Classificação")
        verbose_name_plural = _("Classificações")
        ordering = ["abbreviation"]


class Book(models.Model):
    isbn = models.CharField(
        max_length=13,
        validators=[validate_isbn],
        verbose_name=_("ISBN"),
        null=True,
        blank=True,
    )
    canonical_isbn = models.CharField(
        max_length=13,
        verbose_name=_("ISBN-13 canônico"),
        null=True,
        editable=False,
    )
    title = models.TextField(verbose_name=_("Título"))
    unaccent_title = models.TextField(
        verbose_name=_("Título sem acentos"), editable=False
    )
    author_first_names = models.CharField(
        max_length=1024,
        verbose_name=_("Primeiros nomes do autor"),
        null=True,
        blank=True,
    )
    author_last_name = models.CharField(
        max_length=255, verbose_name=_("Último nome do autor")
    )
    unaccent_author = models.CharField(
        max_length=255, verbose_name=_("Autor sem acento"), editable=False
    )
    publisher = models.CharField(
        max_length=255,
        verbose_name=_("Editora"),
        null=True,
        blank=True,
    )
    classification = models.ForeignKey(
        Classification,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Classificação"),
    )
    code = models.CharField(
        max_length=50,
        verbose_name=_("Código cutter"),
        null=True,
        editable=False,
    )
    creation_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Data de criação")
    )
    last_modified = models.DateTimeField(
        auto_now=True, verbose_name=_("Última modificação")
    )

    def units(self):
        return self.specimens.count()

    def calc_title_first_letters(self, n=1):
        words = self.title.split()
        while words[0].lower() in ARTICLES:
            del words[0]

        letters = "".join(words)
        m = n - len(letters)
        first_letters = unidecode(letters[:n].lower())
        if m > 0:
            first_letters += str(m)

        return first_letters


    def calc_code(self):
        cutcode = cutter.get(self.author_last_name)
        author = self.author_last_name[0].upper()

        n = 1
        while self.__class__.objects.filter(
            code=(
                code := f"{author}{cutcode}{self.calc_title_first_letters(n)}"
            )
        ).exists():
            n += 1

        return code

    @property
    def author(self):
        return f"{self.author_first_names} {self.author_last_name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.calc_code()
        if self.isbn:
            self.isbn = canonical(self.isbn)
            self.canonical_isbn = ean13(self.isbn)
        self.unaccent_author = unidecode(
            f"{self.author_first_names} {self.author_last_name}"
        )
        self.unaccent_title = unidecode(self.title)
        return super().save(*args, **kwargs)

    @property
    def available(self):
        return self.specimens.filter(_available=True).exists()

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = _("Livro")
        verbose_name_plural = _("Livros")
        constraints = [
            models.UniqueConstraint(fields=("isbn",), name="unique_isbn"),
            models.UniqueConstraint(fields=("code",), name="unique_code"),
        ]


# pylint: disable-next=too-few-public-methods
class SpecimenManager(models.Manager):
    """Annotate if specimen is available (`_available`)"""

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        count_returned = Count(
            "loans", filter=Q(loans__return_date__lt=timezone.now())
        )
        qs = qs.annotate(_available=Exact(count_returned, Count("loans")))

        return qs


class Specimen(models.Model):
    objects = SpecimenManager()
    number = models.IntegerField(
        verbose_name=_("Número"),
        default=0,
        validators=[MinValueValidator(0)],
    )
    book = models.ForeignKey(
        Book,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_("Livro"),
        related_name="specimens",
    )

    @property
    def available(self):
        if hasattr(self, "_available"):
            return self._available

        returned_loans = self.loans.filter(return_date__lt=timezone.now())
        all_loans = self.loans.all()
        return all_loans.count() == returned_loans.count()

    def __str__(self):
        return f"E{self.number} | {self.book}"

    def save(self, *args, **kwargs):
        cls = self.__class__
        qs = cls.objects.filter(book=self.book)
        self.number = max(o.number for o in qs) + 1 if qs else 1

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Exemplar")
        verbose_name_plural = _("Exemplares")
        constraints = [
            models.UniqueConstraint(
                fields=("number", "book"), name="unique specimen number"
            ),
        ]
