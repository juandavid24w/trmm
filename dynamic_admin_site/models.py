from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from .apps import DynamicAdminSiteConfig

configuration_fields = {
    "site_header": models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Cabeçalho do site")
    ),
    "site_title": models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Título do site")
    ),
    "site_url": models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Link para o site principal"),
    ),
    "index_title": models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Título da página principal"),
    ),
    "empty_value_display": models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Exibição de valores vazios"),
    ),
    "enable_nav_sidebar": models.BooleanField(
        verbose_name=_("Habilitar barra lateral de navegação"),
    ),
}


def site_configuration_factory(*fields):
    all_fields = configuration_fields.keys()
    if not fields:
        fields = all_fields
    else:
        if not set(fields).issubset(all_fields):
            wrong = [f for f in fields if f not in all_fields]
            raise ImproperlyConfigured(
                f"Received invalid fields: '{wrong}'. Expected "
                + "subset of '{', '.join(all_keys)}'"
            )

    class Meta:
        abstract = True

    return type(
        "SiteConfigurationModel",
        (SingletonModel,),
        {
            **{f: configuration_fields[f] for f in fields},
            "Meta": Meta,
            "__module__": DynamicAdminSiteConfig.name,
        },
    )


SiteConfigurationModel = site_configuration_factory()
