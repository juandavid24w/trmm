from django.contrib.admin.decorators import action
from django.contrib.messages import success
from django.utils.translation import gettext_lazy as _

from .models import Specimen


@action(
    permissions=["change"],
    description=_("Fazer marcação de etiqueta impressa"),
)
def mark_label_printed(_modeladmin, request, queryset):
    Specimen.objects.filter(book__in=queryset).update(label_printed=True)
    success(request, _("Marcações realizadas com sucesso"))


@action(
    permissions=["change"],
    description=_("Remover marcação de etiqueta impressa"),
)
def remove_label_printed(_modeladmin, request, queryset):
    Specimen.objects.filter(book__in=queryset).update(label_printed=False)
    success(request, _("Marcações retiradas com sucesso"))
