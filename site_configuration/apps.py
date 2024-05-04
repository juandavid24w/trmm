from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SiteConfigurationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "site_configuration"
    verbose_name = _("Configurações do site")
