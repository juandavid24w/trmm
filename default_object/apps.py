from django.apps import AppConfig


class DefaultObjectConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "default_object"
