from django import forms
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.decorators import action
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from .models import Classification


class SelectClassificationForm(forms.Form):
    classification = forms.ModelChoiceField(
        queryset=Classification.objects.all().order_by("pk"),
        label=_("Classificação"),
    )


@action(
    permissions=["change"],
    description=gettext_lazy("Alterar classificação"),
)
def change_classification(modeladmin, request, queryset):
    from django.contrib.admin.models import CHANGE, LogEntry

    if not modeladmin.has_change_permission(request):
        messages.error(
            request,
            _(
                "Permissões insuficientes para trocar a classificação dos "
                "livros"
            ),
        )
        return None

    if clsf := request.POST.get("classification"):
        try:
            clsf_obj = Classification.objects.get(pk=clsf)
        except Classification.DoesNotExist:
            messages.error(
                request,
                _("Classficação não existe: %(clsf)s") % {"clsf": clsf},
            )
            return None

        queryset.update(classification=clsf_obj)
        message = _("Alterada a classificação.")
        for obj in queryset:
            modeladmin.log_change(request, obj, message)

        messages.success(
            request,
            _(
                "Livros atualizados para a classificação '%(clsf)s' com sucesso"
            )
            % {"clsf": clsf},
        )
        return None

    form = SelectClassificationForm()
    context = {
        **modeladmin.admin_site.each_context(request),
        "title": _("Alterar classificação de livros"),
        "queryset": queryset,
        "form": form,
        "opts": modeladmin.model._meta,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
    }

    return TemplateResponse(
        request,
        "books/change_classification.html",
        context,
    )
