from django.apps import AppConfig


class DynamicAdminSiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dynamic_admin_site"
