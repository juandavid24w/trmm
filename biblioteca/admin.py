from django.contrib import admin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from dynamic_admin_site.site import DynamicAdminMixin
from public_admin.admin import PublicAdminSiteMixin
from site_configuration.models import SiteConfiguration


class BibliotecaAdminSite(DynamicAdminMixin, admin.AdminSite):
    site_title = _("Biblioteca")
    site_header = _("Biblioteca")
    index_title = _("Administração")

    site_configuration_model = SiteConfiguration

    def each_context(self, request, *args, **kwargs):
        context = super().each_context(request, *args, **kwargs) or {}

        cls = self.site_configuration_model
        context["site_header"] = cls.get_solo().administration_header

        if request.path == reverse("admin:logout"):
            try:
                context["goodbye_msg"] = (
                    SiteConfiguration.get_solo().goodbye_msg
                )
            except SiteConfiguration.DoesNotExist:
                pass

        return context

    def has_permission(self, request):
        return request.user.is_active


class PublicBibliotecaAdminSite(
    DynamicAdminMixin, PublicAdminSiteMixin, admin.AdminSite
):
    site_configuration_model = SiteConfiguration
    site_title = _("Biblioteca Pública")
    site_header = _("Biblioteca Pública")
    index_title = _("Administração")

    def each_context(self, request, *args, **kwargs):
        context = super().each_context(request, *args, **kwargs) or {}
        context["login_url"] = reverse("admin:login")
        context["admin_index_url"] = reverse("admin:index")

        if request.path == reverse("public_admin:index"):
            try:
                context["welcome_msg"] = (
                    SiteConfiguration.get_solo().welcome_msg
                )
            except SiteConfiguration.DoesNotExist:
                pass

        return context

public_site = PublicBibliotecaAdminSite("public_admin")
