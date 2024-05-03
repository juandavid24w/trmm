from django.db import models
from django.forms.models import model_to_dict
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

    def as_dict(self):
        return model_to_dict(self)

    class Meta:
        verbose_name = _("Configuração do site")
