from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    class Grade(models.TextChoices):
        EF6 = "6EF", _("6º ano do ensino fundamental")
        EF7 = "7EF", _("7º ano do ensino fundamental")
        EF8 = "8EF", _("8º ano do ensino fundamental")
        EF9 = "9EF", _("9º ano do ensino fundamental")
        EM1 = "1EM", _("1ª série do ensino médio")
        EM2 = "2EM", _("2ª série do ensino médio")
        EM3 = "3EM", _("3ª série do ensino médio")

        __empty__ = None

        def next(self, reverse=False):
            cls = self.__class__
            if reverse:
                it = iter(reversed(cls))
            else:
                it = iter(cls)

            while next(it) != self:
                continue

            try:
                return next(it)
            except StopIteration:
                return self.__empty__

        def prev(self):
            return self.next(reverse=True)

        @classmethod
        def max_length(cls):
            return max(map(len, cls))

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    grade = models.CharField(
        max_length=Grade.max_length(),
        choices=Grade,
        default=Grade.__empty__,
        null=True,
        verbose_name=_("Série"),
    )

    class Meta:
        verbose_name = _("Perfil")
        verbose_name_plural = _("Perfis")

    def __repr__(self):
        return f"Profile({self.user})"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.grade})"


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
