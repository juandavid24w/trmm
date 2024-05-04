from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from dynamic_admin_site.models import site_configuration_factory

SiteConfigurationModel = site_configuration_factory(
    "site_title", "site_header", "index_title"
)


class SiteConfiguration(SiteConfigurationModel):
    welcome_msg = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Mensagem de boas vindas"),
    )
    goodbye_msg = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Mensagem de despedida"),
    )
    administration_header = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Cabeçalho da administração do site"),
    )

    def __str__(self):
        return gettext("Configuração do site")

    class Meta:
        verbose_name = _("Configuração do site")
