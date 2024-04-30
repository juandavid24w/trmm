from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, DurationField, F, Q, Sum
from django.db.models.functions import Cast
from django.utils.translation import gettext as _

from books.models import Specimen
from profiles.models import Profile


class Period(models.Model):
    description = models.TextField(verbose_name=_("Descrição"), blank=True)
    days = models.IntegerField(
        verbose_name=_("Número de dias"), validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = _("Período")
        verbose_name_plural = _("Períodos")

    def __str__(self):
        return _("%s (%s dias)") % (self.description, self.days)

    @classmethod
    def get_default(cls):
        return cls.objects.all()[0]


class Renewal(models.Model):
    description = models.TextField(verbose_name=_("Descrição"), blank=True)
    days = models.IntegerField(
        verbose_name=_("Número de dias"), validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = _("Renovação")
        verbose_name_plural = _("Renovações")

    def __str__(self):
        return _("%s (%s dias)") % (self.description, self.days)


class LoanManager(models.Manager):  # pylint: disable=too-few-public-methods
    """Annotate due date (`due`) and number of renovations
    (`renewals__count`) to resulting querysets
    """

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        renewals = Sum("renewals__days", default=0)
        duration = Cast(
            timedelta(days=1) * (renewals + F("duration__days")),
            output_field=DurationField(),
        )
        qs = qs.annotate(due=F("date") + duration)
        qs = qs.annotate(Count("renewals"))
        qs = qs.annotate(returned=Q(return_date__isnull=False))

        return qs


class Loan(models.Model):
    objects = LoanManager()

    specimen = models.ForeignKey(
        Specimen,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Exemplar"),
        related_name="loans",
    )
    duration = models.ForeignKey(
        Period,
        on_delete=models.RESTRICT,
        verbose_name=_("Duração"),
    )
    renewals = models.ManyToManyField(
        Renewal,
        blank=True,
        verbose_name=_("Renovações"),
    )
    date = models.DateTimeField(verbose_name=_("Data do empréstimo"))
    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, verbose_name=_("Usuário")
    )
    return_date = models.DateTimeField(
        verbose_name=_("Data de devolução"),
        default=None,
        null=True,
        blank=True,
    )

    def clean(self):
        # pytlint: disable-next=no-member # available is manager's annotation
        if not self.specimen.available:
            raise ValidationError(_("Exemplar já está alugado"))

    class Meta:
        verbose_name = _("Empréstimo")
        verbose_name_plural = _("Empréstimos")

    def __str__(self):
        return _("Empréstimo de %s") % self.user
