from django.contrib import admin
from django.core.files.base import ContentFile
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from fpdf import FPDFException
from huey.contrib.djhuey import db_task

from default_object.admin import DefaultObjectAdminMixin

from .labels import create
from .models import LabelPageConfiguration, LabelPrint


@admin.register(LabelPageConfiguration)
class LabelPageConfigurationAdmin(DefaultObjectAdminMixin, admin.ModelAdmin):
    pass


@db_task()
def generate_label(obj_id):
    qs = LabelPrint.objects.filter(pk=obj_id)
    obj = qs.first()

    if obj.n_labels() > 0:
        try:
            content, count = create(obj)
        except FPDFException as e:
            msg = gettext("Erro na geração de etiquetas: %(error)s") % {
                "error": str(e)
            }
            qs.update(status=msg)
            return

        if count <= 0:
            msg = gettext(
                "Não havia exemplares marcados para geração, então "
                "nenhuma etiqueta foi gerada."
            )

            qs.update(status=str(msg))
            return

        obj.labels_file.save(
            # Translators: Labels download filename
            name=gettext("etiquetas") + ".pdf",
            content=ContentFile(content),
            save=True,
        )

        msg = gettext("Etiquetas geradas com sucesso.")
        qs.update(status=msg)
        return

    msg = gettext(
        "Erro na geração de etiquetas: nenhum exemplar foi escolhido!"
    )
    obj.update(status=msg)


@admin.register(LabelPrint)
class LabelPrintAdmin(admin.ModelAdmin):
    change_list_template = "labels/change_list.html"
    change_form_template = "labels/change_form.html"
    readonly_fields = ["n_labels", "labels_file", "admin_status"]
    list_display = [
        "__str__",
        "n_labels",
        "created",
        "configuration",
        "labels_file",
    ]

    @admin.display(description=_("Status do processamento"))
    def admin_status(self, obj):
        return mark_safe(obj.status)

    def has_add_permission(self, _request, _obj=None):
        return False

    def change_view(
        self, request, object_id, form_url="", extra_context=None
    ):
        context = extra_context or {}
        context["save_button_label"] = gettext("Gerar etiquetas")
        context["show_save"] = False
        return super().change_view(request, object_id, form_url, context)

    def save_model(self, request, obj, form, change):
        obj.status = format_html(
            '{}<a href="">{}</a>{}',
            gettext("Processando etiquetas de %(count)d exemplares. ")
            % {"count": obj.n_labels()},
            gettext("Recarregue"),
            gettext(
                " a página em alguns minutos para consultar o resultado."
            ),
        )
        obj.labels_file.delete()
        super().save_model(request, obj, form, change)
        generate_label(obj.pk)

    @admin.display(description=_("Nº de exemplares"))
    def n_labels(self, obj):
        return obj.n_labels()

    class Media:
        js = ["labels/script.js"]
