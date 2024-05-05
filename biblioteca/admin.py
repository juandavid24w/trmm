from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from dynamic_admin_site.site import DynamicAdminMixin
from public_admin.admin import PublicAdminSiteMixin
from site_configuration.models import EmailConfiguration, SiteConfiguration


class AuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super(AdminAuthenticationForm, self).confirm_login_allowed(user)


class BibliotecaAdminSite(DynamicAdminMixin, admin.AdminSite):
    site_title = _("Biblioteca")
    site_header = _("Biblioteca")
    index_title = _("Administração")

    login_form = AuthenticationForm
    site_configuration_model = SiteConfiguration

    def each_context(self, request, *args, **kwargs):
        context = super().each_context(request, *args, **kwargs) or {}

        cls = self.site_configuration_model
        context["site_header"] = cls.get_solo().administration_header

        if request.path == reverse("admin:logout"):
            context["goodbye_msg"] = SiteConfiguration.get_solo().goodbye_msg

        if request.path == reverse("admin:login"):
            context["email_activated"] = (
                EmailConfiguration.get_solo().activated
            )

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
