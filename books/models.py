from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext as _

from . import cutter
from .language import ARTICLES
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
    title_first_letter = models.CharField(
        max_length=1,
        verbose_name=_("Primeira letra do título"),
        help_text=_(
            "Primeira letra da primeira palavra do título que não é um artigo"
        ),
    )
    code = models.CharField(
        max_length=50,
        verbose_name=_("Código parcial do livro"),
        help_text=_("Código do livro sem o número de exemplar"),
        null=True,
    )
    creation_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Data de criação")
    )
    last_modified = models.DateTimeField(
        auto_now=True, verbose_name=_("Última modificação")
    )

    def units(self):
        return self.specimens.count()

    def calc_title_first_letter(self):
        words = self.title.split()
        while words[0].lower() in ARTICLES:
            del words[0]
        return words[0][0].lower()

    def calc_code(self):
        cl = self.classification.name
        loc = self.classification.location.name
        cutcode = cutter.get(self.author_last_name)
        title = self.title_first_letter
        author = self.author_last_name[0].upper()

        return f"{cl} {author}{cutcode}{title}%s {loc}"

    @property
    def author(self):
        return f"{self.author_first_names} {self.author_last_name}"

    def save(self, *args, **kwargs):
        self.title_first_letter = self.calc_title_first_letter()
        if not self.code:
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
    code = models.CharField(
        max_length=50, verbose_name=_("Código"), default="", blank=True
    )

    def __str__(self):
        return f"E{self.number} | {self.book}"

    def save(self, *args, **kwargs):
        cls = self.__class__
        qs = cls.objects.filter(book=self.book)
        self.number = max(o.number for o in qs) + 1 if qs else 1
        if not self.code:
            self.code = self.book.code % self.number

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Exemplar")
        verbose_name_plural = _("Exemplares")
        constraints = [
            models.UniqueConstraint(
                fields=("number", "book"), name="unique specimen number"
            ),
        ]
