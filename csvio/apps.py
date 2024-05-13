from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CsvioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "csvio"
    verbose_name = _("Importação e exportação")
