from django.apps import AppConfig


class HiddenAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hidden_admin"
