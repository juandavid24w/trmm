from datetime import datetime

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class LoanStatusFilter(admin.SimpleListFilter):
    title = _("status do empréstimo")
    parameter_name = "loan_status"
    default_lookup = "not_returned"

    def lookups(self, *args):
        return [
            ("not_returned", _("Não devolvidos")),
            ("late", _("Atrasados")),
            ("running", _("No prazo")),
            ("all", _("Todos")),
            ("returned", _("Devolvidos")),
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
            case "all":
                return queryset
            case "not_returned" | _:
                return queryset.filter(returned=False)

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": (
                    self.value() == str(lookup)
                    or (
                        self.value() is None
                        and str(lookup) == self.default_lookup
                    )
                ),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }
