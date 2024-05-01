from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel


class SiteConfiguration(SingletonModel):
    site_title = models.CharField(
        max_length=255, null=True, verbose_name=_("Título do site")
    )
    site_header = models.CharField(
        max_length=255, null=True, verbose_name=_("Cabeçalho do site")
    )
    index_title = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_("Título da página principal"),
    )

    def __str__(self):
        return gettext("Configuração do site")

    class Meta:
        verbose_name = _("Configuração do site")
