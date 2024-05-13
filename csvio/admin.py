from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .io import csv_import
from .models import CSVExport, CSVImport
from .registry import CSVIORegistry


@admin.register(CSVImport)
class CSVImportAdmin(admin.ModelAdmin):
    change_form_template = "csvio/change_form.html"
    add_form_template = "csvio/change_form.html"
    readonly_fields = ["error_file"]

    @property
    def model_fields_data(self):
        return CSVIORegistry.get_model_fields(export=False)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        form.base_fields["key"].help_text = format_html(
            '{}: <span id="mandatory-fields"></span><br>'
            '{}: <span id="optional-fields"></span>',
            _("Colunas obrigatórias"),
            _("Colunas opcionais"),
        )

        return form

    def save_model(self, request, obj, *args, **kwargs):
        super().save_model(request, obj, *args, **kwargs)
        try:
            csv_import(request, obj)
            model = obj.get_model()
            messages.success(
                request,
                _("%(objects)s importados com sucesso")
                % {"objects": model._meta.verbose_name_plural},
            )
        except ValidationError as e:
            for msg in e:
                messages.error(request, msg)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj is None:
            return [f for f in fields if f != "error_file"]
        return fields

    def change_view(
        self, request, object_id, form_url="", extra_context=None
    ):
        extra_context = extra_context or {}
        extra_context["csvio_data"] = self.model_fields_data

        return super().change_view(
            request, object_id, form_url, extra_context
        )

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["csvio_data"] = self.model_fields_data

        return super().add_view(request, form_url, extra_context)

    class Media:
        js = ["csvio/script.js"]


@admin.register(CSVExport)
class CSVExportAdmin(admin.ModelAdmin):
    fields = ["name", "key", "file"]
    readonly_fields = ["file"]
