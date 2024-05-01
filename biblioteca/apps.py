from django.contrib.admin.apps import AdminConfig


class BibliotecaAdminConfig(AdminConfig):
    default_site = "biblioteca.admin.BibliotecaAdminSite"
