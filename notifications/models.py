from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from loans.models import Loan


class Trigger(models.Model):
    class TriggerChoices(models.IntegerChoices):
        DUE_IN_N = 1, _("Expira em <n> dias")
        LATE_AFTER_N = 2, _("Atrasado há <n> dias")
        LATE_AFTER_EACH_N = 3, _("Atrasado a cada <n> dias")

        def get_queryset(self, querysets, n, log):
            """
            querysets: dict with two keys: running and late, each
            containting loans which are note yet returned and which are
            late, respectively

            n: n parameter from notification

            log: queryset of logs associated with this notification
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

    ttype = models.IntegerField(
        choices=TriggerChoices,
        verbose_name=_("tipo de gatilho"),
    )

    def __str__(self):
        return self.get_ttype_display()

    class Meta:
        verbose_name = _("Gatilho")
        verbose_name_plural = _("Gatilhos")
        constraints = [
            models.UniqueConstraint(fields=("ttype",), name="unique ttype"),
        ]


class Notification(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nome"))
    subject = models.CharField(max_length=100, verbose_name=_("Assunto"))
    message = HTMLField(
        verbose_name=_("Mensagem"),
        help_text=_(
            "Variáveis disponíveis: {{ name }}, {{ signature }}"
            + "{{ site_title }}, {{ due }} e {{ book }}"
            + "{{ late_days }}"
        ),
    )
    n_parameter = models.IntegerField(
        verbose_name=_("Parâmetro <n>"), blank=True, null=True
    )
    triggers = models.ManyToManyField(Trigger)

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
