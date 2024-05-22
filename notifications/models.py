from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from loans.models import Loan

from .context import get_context


class Notification(models.Model):
    class TriggerChoices(models.IntegerChoices):
        DUE_IN_N = 1, _("Expira em <n> dias")
        LATE_AFTER_N = 2, _("Atrasado há <n> dias")
        LATE_AFTER_EACH_N = 3, _("Atrasado a cada <n> dias")
        LOAN_RECEIPT = 4, _("Recibo de empréstimo")
        RETURN_RECEIPT = 5, _("Recibo de devolução")
        RENEWAL_RECEIPT = 6, _("Recibo de renovação")

        def get_queryset(self, querysets, n, log):
            """
            querysets: dict with two keys: running and late, each
            containting loans which are note yet returned and which are
            late, respectively

            n: field n

            log: queryset of logs associated with this notification

            returns the queryset of loans to be notified
            """
            match self:
                case self.DUE_IN_N:
                    qs = querysets["running"].filter(
                        due__lt=timezone.now() + timedelta(days=n)
                    )
                    qs = qs.exclude(
                        user__in=log.values_list("loan__user", flat=True)
                    )

                    return qs
                case self.LATE_AFTER_N:
                    qs = querysets["late"].filter(
                        due__lt=timezone.now() - timedelta(days=n)
                    )
                    qs = qs.exclude(
                        user__in=log.values_list("loan__user", flat=True)
                    )
                    return qs
                case self.LATE_AFTER_EACH_N:
                    qs = querysets["late"].filter(
                        due__lt=timezone.now() - timedelta(days=n)
                    )
                    qs = qs.exclude(
                        user__in=log.filter(
                            created__gt=timezone.now() - timedelta(days=n)
                        ).values_list("loan__user", flat=True)
                    )

                    return qs

                case _:
                    return []

    name = models.CharField(max_length=100, verbose_name=_("Nome"))
    subject = models.CharField(max_length=100, verbose_name=_("Assunto"))
    message = HTMLField(
        verbose_name=_("Mensagem"),
        help_text=format_html(
            "{}<code>{}</code>",
            _("Variáveis disponíveis: "),
            ", ".join(
                "{{ %s }}" % k
                for k in sorted(get_context().flatten().keys())
                if k not in ("True", "False", "None")
            ),
        ),
    )
    n_parameter = models.IntegerField(
        verbose_name=_("Parâmetro <n>"),
        help_text=_("Só é utilizado se o tipo de gatilho contiver '<n>'"),
        blank=True,
        null=True,
        validators=[MinValueValidator],
    )
    trigger = models.IntegerField(
        choices=TriggerChoices,
        verbose_name=_("tipo de gatilho"),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Notificação")
        verbose_name_plural = _("Notificações")


class NotificationLog(models.Model):
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Data"))
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        verbose_name=_("Empréstimo"),
    )
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, verbose_name=_("Notificação")
    )

    def __str__(self):
        return gettext("Registro: %(user)s | %(created)s") % {
            "user": self.loan.user.profile,
            "created": self.created.strftime("%d/%m/%y %H:%M"),
        }

    class Meta:
        verbose_name = _("Registro de notificação")
        verbose_name_plural = _("Registros de notificação")
