from datetime import time
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.html import format_html
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField
from solo.models import SingletonModel
from tinymce.models import HTMLField

from dynamic_admin_site.models import site_configuration_factory

from .backups import BACKUP_PATH, get_version

SiteConfigurationModel = site_configuration_factory(
    "site_title", "site_header", "index_title"
)


class SiteConfiguration(SiteConfigurationModel):
    administration_header = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Cabeçalho da administração do site"),
    )
    favicon = models.ImageField(
        verbose_name=_("Favicon"),
        upload_to="site_configuration",
        null=True,
        blank=True,
    )
    working_days = MultiSelectField(
        verbose_name=_("Dias de funcionamento"),
        choices=(
            (1, _("Domingo")),
            (2, _("Segunda-feira")),
            (3, _("Terça-feira")),
            (4, _("Quarta-feira")),
            (5, _("Quinta-feira")),
            (6, _("Sexta-feira")),
            (7, _("Sábado")),
        ),
        default="2,3,4,5,6",
    )
    ending_hour = models.TimeField(
        verbose_name=_("Horário de fim de funcionamento"),
        default=time(18, 0),
    )
    welcome_msg = HTMLField(
        null=True,
        blank=True,
        verbose_name=_("Mensagem de boas vindas"),
    )
    goodbye_msg = HTMLField(
        null=True,
        blank=True,
        verbose_name=_("Mensagem de despedida"),
    )

    def get_working_days(self):
        wd = self.working_days
        if isinstance(wd, str):
            wd = wd.split(",")
        return list(map(int, wd))

    def __str__(self):
        return gettext("Configuração do site")

    class Meta:
        verbose_name = _("Configuração do site")


class EmailConfiguration(SingletonModel):
    activated = models.BooleanField(
        default=False,
        verbose_name=_("Email está ativado?"),
        help_text=_(
            "Só ative essa opção depois de testar as configurações de "
            + "email no botão ao lado. Quando ativado, as notificações vão "
            + "ser enviadas por email e será possível a usuários "
            + "redefinir suas senhas."
        ),
    )
    host = models.CharField(
        max_length=128,
        verbose_name=_("Host"),
        default="smtp.gmail.com",
    )
    port = models.PositiveIntegerField(verbose_name=_("Porta"), default=587)
    username = models.CharField(
        max_length=128,
        verbose_name=_("Usuário"),
        default="example@gmail.com",
    )
    password = models.CharField(
        max_length=128,
        verbose_name=_("Senha"),
        default="1234",
    )
    use_tls = models.BooleanField(
        default=True,
        verbose_name=_("Usar TLS"),
    )
    use_ssl = models.BooleanField(
        default=False,
        verbose_name=_("Usar SSL"),
    )
    timeout = models.IntegerField(
        blank=True,
        null=True,
        default=120,
        verbose_name=_("Timeout"),
    )
    from_name = models.CharField(
        max_length=255,
        verbose_name=_("Nome do remetente"),
        default=_("Biblioteca"),
        null=True,
        blank=True,
    )
    from_email = models.EmailField(
        verbose_name=_("Email remetente"),
        default="admin@example.com",
    )
    signature = HTMLField(
        blank=True,
        null=True,
        verbose_name=_("Assinatura dos emails"),
        help_text=format_html(
            "{}<code>{}</code>{}",
            _(
                "Para usar essa assinatura em seus emails, utilize a variável "
            ),
            "{{ signature }}",
            ".",
        ),
    )

    def __str__(self):
        return gettext("Configurações de email")

    class Meta:
        verbose_name = _("Configurações de email")


class DocumentationPage(models.Model):
    order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
        verbose_name=_("Ordem"),
    )
    title = models.CharField(
        max_length=100,
        verbose_name=_("Título"),
    )
    text = HTMLField(
        null=True,
        blank=True,
        verbose_name=_("Mensagem"),
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Página de documentação")
        verbose_name_plural = _("Documentação")
        ordering = ["order"]


class Backup(models.Model):
    name = models.CharField(
        max_length=127,
        verbose_name=_("Nome"),
        blank=True,
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Data de criação")
    )
    dump = models.FileField(
        verbose_name=_("Arquivo de backup"),
        blank=True,
        upload_to=BACKUP_PATH,
    )
    status = models.CharField(
        max_length=256,
        editable=False,
        blank=True,
        default="",
        verbose_name=_("Status do processamento"),
    )

    def clean(self):
        if not self.name and not self.dump.name:
            raise ValidationError(
                {"name": _("Por favor, use algum nome para esse backup")}
            )

        if not self.name and self.dump.name:
            self.name = Path(self.dump.name).with_suffix("").name

        return super().clean()

    def __str__(self):
        return self.name

    def version(self):
        if self.dump.name:
            return get_version(self)
        return None

    class Meta:
        verbose_name = _("Backup")
        verbose_name_plural = _("Backups")
        constraints = [
            models.UniqueConstraint(fields=["name"], name="unique_name"),
        ]


@receiver(pre_delete, sender=Backup)
def delete_files_hook(sender, instance, *args, **kwargs):
    try:
        (settings.MEDIA_ROOT / instance.dump.name).unlink()
    except OSError:
        pass
