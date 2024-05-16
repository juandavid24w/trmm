from django.contrib import admin
from django.http import FileResponse
from django.utils.translation import gettext_lazy as _

from admin_buttons.admin import AdminButtonsMixin
from default_object.admin import DefaultObjectAdminMixin

from .models import LabelPageConfiguration, LabelPrint


@admin.register(LabelPageConfiguration)
class LabelPageConfigurationAdmin(DefaultObjectAdminMixin, admin.ModelAdmin):
    pass


@admin.register(LabelPrint)
class LabelPrintAdmin(AdminButtonsMixin, admin.ModelAdmin):
    change_list_template = "labels/change_list.html"
    readonly_fields = ["labels_file"]
    list_display = [
        "__str__",
        "n_labels",
        "created",
        "configuration",
        "labels_file",
    ]

    def has_add_permission(self, _request, _obj=None):
        return False

    def save_and_download(self, _request, obj):
        return FileResponse(obj.labels_file.open())

    @admin.display(description=_("Nº de exemplares"))
    def n_labels(self, obj):
        return obj.specimens.count()

    admin_buttons_config = [
        {
            "name": "_saveanddownload",
            "label": _("Salvar e fazer download"),
            "method": "save_and_download",
            "use_separator": False,
        }
    ]
