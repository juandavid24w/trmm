from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel
from tinymce.models import HTMLField

from dynamic_admin_site.models import site_configuration_factory

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
    port = models.PositiveIntegerField(verbose_name=_("Senha"), default=587)
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
    from_email = models.EmailField(
        verbose_name=_("Email remetente"),
        default="admin@example.com",
    )
    signature = HTMLField(
        blank=True,
        null=True,
        verbose_name=_("Assinatura dos email"),
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
