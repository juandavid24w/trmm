from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from dynadmin.site import DynamicAdminMixin


class BibliotecaAdminSite(DynamicAdminMixin, admin.AdminSite):
    site_title = _("Biblioteca")
    site_header = _("Biblioteca")
    index_title = _("Administração")

    def has_permission(self, request):
        return request.user.is_active
