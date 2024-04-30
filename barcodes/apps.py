from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BarcodesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "barcodes"
    verbose_name = _("Código de barras")
