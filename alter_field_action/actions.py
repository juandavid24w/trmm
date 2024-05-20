from django import forms
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.decorators import action
from django.db import models
from django.template.response import TemplateResponse
from django.utils.functional import lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

capitalize = lazy(str.title, str)

def alter_field_action(model, field_name, form_field=None):
    field = model._meta.get_field(field_name)
    is_m2m = isinstance(field, models.ManyToManyField)
    verb = _("adicionar") if is_m2m else _("alterar")
    form_field = form_field or field.formfield()

    if isinstance(field, models.OneToOneField):
        raise ValueError(
            "Cannot assign the same value to a one-to-one field of "
            "multiple objects."
        )

    fmt = {
        "field": field.verbose_name,
        "model": model._meta.verbose_name_plural,
        "verb": verb,
        "verb_title": capitalize(verb),
    }

    class SelectClassificationForm(forms.Form):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields[field_name] = form_field

    @action(
        permissions=["change"],
        # Translators: example: alter classification
        description=gettext_lazy("%(verb_title)s %(field)s") % fmt,
    )
    def alter_field(modeladmin, request, queryset):
        if not modeladmin.has_change_permission(request):
            messages.error(
                request,
                _(
                    "Permissões insuficientes para %(verb)s %(field)s "
                    "em %(model)s"
                )
                % fmt,
            )

        if request.POST.get(field_name):
            form = SelectClassificationForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                if is_m2m:
                    for obj in queryset:
                        getattr(obj, field_name).add(*data[field_name])
                else:
                    queryset.update(**{field_name: data[field_name]})
                messages.success(
                    request,
                    _(
                        "%(model)s atualizados para %(field)s '%(value)s' "
                        "com sucesso"
                    )
                    % {
                        "value": (
                            ", ".join(str(o) for o in data[field_name])
                            if isinstance(data[field_name], models.QuerySet)
                            else data[field_name]
                        ),
                        **fmt,
                    },
                )
                return None

        else:
            form = SelectClassificationForm()

        context = {
            **modeladmin.admin_site.each_context(request),
            # Translators: example: alter classification of books
            "title": _("%(verb_title)s %(field)s em %(model)s") % fmt,
            "queryset": queryset,
            "form": form,
            "opts": modeladmin.model._meta,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "field_name": field_name,
            "change_message": _("Alterando os seguintes %(model)s:") % fmt,
            "verb": capitalize(verb),
        }

        return TemplateResponse(
            request,
            "alter_field_action/alter_field.html",
            context,
        )

    alter_field.__name__ = f"alter_field_{field_name}"
    return alter_field
