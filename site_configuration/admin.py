from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions, action
from solo.admin import SingletonModelAdmin

from .models import DocumentationPage, SiteConfiguration

admin.site.register(SiteConfiguration, SingletonModelAdmin)


class DocumentationChangeList(ChangeList):
    def url_for_result(self, result):
        url = super().url_for_result(result)
        return f"{url}?detail=true"


@admin.register(DocumentationPage)
class DocumentationAdmin(
    DjangoObjectActions, SortableAdminMixin, admin.ModelAdmin
):
    change_form_template = "site_configuration/change_form.html"
    change_actions = ["to_edit_action", "to_detail_action"]

    @action(label=_("Editar"), description=_("Editar essa documentação"))
    def to_edit_action(self, request, obj):
        base = reverse(
            "admin:site_configuration_documentationpage_change",
            args=(obj.pk,),
        )
        return redirect(f"{base}")

    @action(
        label=_("Visualizar"), description=_("Visualizar essa documentação")
    )
    def to_detail_action(self, request, obj):
        base = reverse(
            "admin:site_configuration_documentationpage_change",
            args=(obj.pk,),
        )
        return redirect(f"{base}?detail=true")

    def get_change_actions(self, request, object_id=None, form_url=""):
        if request.GET.get("detail", False):
            return ["to_edit_action"]
        return ["to_detail_action"]

    def get_changelist(self, request, **kwargs):
        return DocumentationChangeList

    def has_change_permission(self, request, obj=None):
        if request.GET.get("detail", False):
            return False
        return super().has_change_permission(request, obj)
