from django.contrib import admin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from dynamic_admin_site.site import DynamicAdminMixin
from public_admin.admin import PublicAdminSiteMixin
from site_configuration.models import SiteConfiguration


class BibliotecaAdminSite(DynamicAdminMixin, admin.AdminSite):
    site_configuration_model = SiteConfiguration
    site_title = _("Biblioteca")
    site_header = _("Biblioteca")
    index_title = _("Administração")

    def has_permission(self, request):
        return request.user.is_active


class PublicBibliotecaAdminSite(
    DynamicAdminMixin, PublicAdminSiteMixin, admin.AdminSite
):
    site_configuration_model = SiteConfiguration
    site_title = _("Biblioteca Pública")
    site_header = _("Biblioteca Pública")
    index_title = _("Administração")

    def each_context(self, *args, **kwargs):
        context = super().each_context(*args, **kwargs) or {}
        context["login_url"] = reverse("admin:login")

        return context


public_site = PublicBibliotecaAdminSite("public_admin")
