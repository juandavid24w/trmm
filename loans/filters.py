from datetime import datetime

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class LoanStatusFilter(admin.SimpleListFilter):
    title = _("status do empréstimo")
    parameter_name = "loan_status"

    def lookups(self, *args):
        return [
            ("returned", _("Devolvidos")),
            ("late", _("Atrasados")),
            ("running", _("Emprestados")),
        ]

    def queryset(self, request, queryset):
        match self.value():
            case "returned":
                return queryset.filter(returned=True)
            case "late":
                return queryset.filter(returned=False, due__lt=datetime.now())
            case "running":
                return queryset.filter(
                    returned=False, due__gte=datetime.now()
                )
            case _:
                return queryset
