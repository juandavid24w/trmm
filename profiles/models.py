from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    id_number = models.CharField(
        max_length=64,
        verbose_name=_("Número de registro"),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Perfil")
        verbose_name_plural = _("Perfis")

    def __repr__(self):
        return f"Profile({self.user})"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Email(models.Model):
    email = models.EmailField()
    receive_notifications = models.BooleanField(
        default=True, verbose_name=_("Receber notificações")
    )
    profile = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="additional_emails",
    )

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _("Email adicional")
        verbose_name_plural = _("Emails adicionais")
