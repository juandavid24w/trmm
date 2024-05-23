from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, DurationField, F, Q, Sum, When
from django.db.models.functions import Cast, ExtractWeekDay
from django.db.models.lookups import In
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from books.models import Book, Classification, Collection, Location, Specimen
from default_object.models import DefaultObjectMixin
from site_configuration.models import SiteConfiguration

User = get_user_model()


class Period(DefaultObjectMixin, models.Model):
    class LogicalOperatorChoices(models.IntegerChoices):
        OR = 1, _("ou")
        AND = 2, _("e")

    description = models.TextField(
        verbose_name=_("Descrição"),
        default=_("Período normal"),
        blank=False,
    )
    days = models.IntegerField(
        verbose_name=_("Número de dias"),
        validators=[MinValueValidator(0)],
        default=15,
    )
    logical_operator = models.IntegerField(
        verbose_name=_("Operador lógico"),
        help_text=_(
            "Indica se vale esse período quando qualquer uma das "
            "condições abaixo for respeitada ('ou'), ou se vale esse "
            "periodo quando todas elas forem respeitadas ('e')"
        ),
        choices=LogicalOperatorChoices,
        default=LogicalOperatorChoices.OR,
        blank=True,
    )
    collections = models.ManyToManyField(
        Collection,
        verbose_name=_("Acervos"),
        blank=True,
    )
    locations = models.ManyToManyField(
        Location,
        verbose_name=_("Localizações"),
        blank=True,
    )
    classifications = models.ManyToManyField(
        Classification,
        verbose_name=_("Classificações"),
        blank=True,
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("Grupos"),
        blank=True,
    )
    users = models.ManyToManyField(
        User,
        verbose_name=_("Usuários"),
        blank=True,
    )
    books = models.ManyToManyField(
        Book,
        verbose_name=_("Livros"),
        blank=True,
    )
    specimens = models.ManyToManyField(
        Specimen,
        verbose_name=_("Exemplares"),
        blank=True,
    )
    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
        verbose_name=_("Ordem"),
    )

    def get_condition_fields(self):
        return [
            f.name
            for f in self._meta.get_fields()
            if isinstance(f, models.ManyToManyField) and f.name != "renewals"
        ]

    def is_empty(self):
        return not any(
            getattr(self, f).exists() for f in self.get_condition_fields()
        )

    def matches(self, specimen, user):
        objects = {
            "collections": [specimen.book.collection],
            "locations": [specimen.book.classification.location],
            "classifications": [specimen.book.classification],
            "groups": [*user.groups.all()],
            "users": [user],
            "books": [specimen.book],
            "specimens": [specimen],
        }

        compare = [
            (f, [o.pk for o in objects[f]])
            for f in self.get_condition_fields()
        ]

        quantifier, is_and = (
            (all, True)
            if self.logical_operator == self.LogicalOperatorChoices.AND
            else (any, False)
        )

        if is_and and self.is_empty():
            return False

        return quantifier(
            (is_and and not getattr(self, field).exists())
            or getattr(self, field).filter(pk__in=pks).exists()
            for field, pks in compare
        )

    @classmethod
    def select_period(cls, specimen, user):
        try:
            return next(
                p for p in cls.objects.all() if p.matches(specimen, user)
            )
        except StopIteration:
            return cls.get_default()

    class Meta:
        verbose_name = _("Período")
        verbose_name_plural = _("Períodos")
        ordering = ["order"]

    def __str__(self):
        return _("%s (%s dias)") % (self.description, self.days)


class Renewal(models.Model):
    description = models.CharField(
        max_length=128,
        verbose_name=_("Descrição"),
        blank=True,
    )
    days = models.IntegerField(
        verbose_name=_("Número de dias"),
        validators=[MinValueValidator(0)],
        default=15,
    )
    period = models.ForeignKey(
        Period,
        verbose_name=_("Período"),
        on_delete=models.CASCADE,
        related_name="renewals",
    )
    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
        verbose_name=_("Ordem"),
    )

    class Meta:
        verbose_name = _("Renovação")
        verbose_name_plural = _("Renovações")
        ordering = ["order"]

    def __str__(self):
        return _("%s (%s dias)") % (self.description, self.days)


class LoanManager(models.Manager):  # pylint: disable=too-few-public-methods
    """Annotate due date (`due`), number of renovations
    (`renewals__count`) and late bool (`late`) to resulting querysets
    """
    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)

        conf = SiteConfiguration.get_solo()
        working_days = conf.get_working_days()

        renewals = Sum("renewals__days", default=0)
        duration = Cast(
            timedelta(days=1) * (renewals + F("period__days")),
            output_field=DurationField(),
        )
        qs = qs.annotate(exact_due=F("date") + duration)

        diff = Cast(
            (conf.ending_hour - F("exact_due__time")),
            output_field=DurationField(),
        )

        is_before = Q(exact_due__time__lt=conf.ending_hour)
        is_after = Q(exact_due__time__gte=conf.ending_hour)

        def is_in(i):
            return In(
                ExtractWeekDay(F("exact_due") + timedelta(days=i)),
                working_days,
            )

        due = Case(
            *(
                When(
                    (is_before & is_in(i)),
                    then=F("exact_due") + diff + timedelta(days=i),
                )
                for i in range(0, 7)
            ),
            *(
                When(
                    (is_after & is_in(i)),
                    then=F("exact_due") + diff + timedelta(days=i),
                )
                for i in range(1, 8)
            ),
            default="exact_due",
            output_field=models.DateTimeField(),
        )

        qs = qs.annotate(due=due)
        qs = qs.annotate(Count("renewals"))
        qs = qs.annotate(returned=Q(return_date__isnull=False))
        qs = qs.annotate(late=Q(returned=False) & Q(due__lt=timezone.now()))

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
    period = models.ForeignKey(
        Period,
        on_delete=models.RESTRICT,
        verbose_name=_("Duração"),
        editable=False,
    )
    renewals = models.ManyToManyField(
        Renewal,
        blank=True,
        editable=False,
        verbose_name=_("Renovações"),
    )
    date = models.DateTimeField(
        verbose_name=_("Data do empréstimo"),
        default=timezone.now,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Usuário"),
    )
    return_date = models.DateTimeField(
        verbose_name=_("Data de devolução"),
        default=None,
        null=True,
        blank=True,
    )

    def clean(self):
        if (
            self._state.adding
            and self.specimen
            and not self.specimen.available
        ):
            raise ValidationError(_("Exemplar já está alugado"))

    def renew(self):
        renewals = list(self.renewals.all())
        n = len(renewals)

        # Disallow renewing if next renewal isn't due yet
        if n > 0:
            days = self.period.days + sum(r.days for r in renewals[:-1])
            if timezone.now() < self.date + timedelta(days=days):
                return _("última renovação ainda não começou")

        last_order = renewals[n - 1].order if n > 0 else -1
        nxt = self.period.renewals.filter(order__gt=last_order).first()

        if not nxt:
            return _("já fez todas as renovações possíveis")

        self.renewals.add(nxt)

        return None

    def unrenew(self):
        renewal = self.renewals.all().last()
        if not renewal:
            return _("não há renovações para serem retiradas")

        self.renewals.remove(renewal)
        return None

    def save(self, *args, **kwargs):
        if self.period_id is None:
            self.period = Period.select_period(self.specimen, self.user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Empréstimo")
        verbose_name_plural = _("Empréstimos")

    def __str__(self):
        return _("Empréstimo de %s") % self.user
