from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from barcodes.admin import BarcodeSearchBoxAdmin

from .filters import LoanStatusFilter
from .models import Loan, Period, Renewal


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ["description", "days"]


@admin.register(Renewal)
class RenewalAdmin(PeriodAdmin):
    list_display = ["description", "days"]


@admin.action(description=_("Marcar devolução"))
def make_returned(_modeladmin, _request, queryset):
    queryset.filter(return_date__isnull=True).update(
        return_date=timezone.now()
    )


@admin.register(Loan)
class LoanAdmin(BarcodeSearchBoxAdmin):
    autocomplete_fields = ["specimen", "user"]
    ordering = ["-date"]
    list_display = [
        "user",
        "title",
        "author",
        "isbn",
        "short_date",
        "short_due",
        "short_return_date",
        "n_renovations",
    ]
    list_filter = [
        LoanStatusFilter,
        "date",
        ("user", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "user__user__first_name",
        "user__user__last_name",
        "specimen__book__title",
        "specimen__book__author_first_names",
        "specimen__book__author_last_name",
        "specimen__book__isbn",
    ]
    formfield_overrides = {
        models.ManyToManyField: {"widget": CheckboxSelectMultiple}
    }

    actions = [make_returned]

    @admin.display(description=_("Vencimento"))
    def due(self, obj):
        return obj.due

    @admin.display(description=_("Título"), ordering="specimen__book__title")
    def title(self, obj):
        return obj.specimen.book.title

    @admin.display(
        description=_("Autor"), ordering="specimen__book__author_last_name"
    )
    def author(self, obj):
        return obj.specimen.book.author

    @admin.display(description=_("ISBN"))
    def isbn(self, obj):
        return obj.specimen.book.isbn

    @admin.display(description=_("Empréstimo"), ordering="date")
    def short_date(self, obj):
        return obj.date.strftime("%d/%m/%y")

    @admin.display(description=_("Vencimento"), ordering="due")
    def short_due(self, obj):
        return obj.due.strftime("%d/%m/%y")

    @admin.display(description=_("Devolução"), ordering="return_date")
    def short_return_date(self, obj):
        if obj.return_date:
            return obj.return_date.strftime("%d/%m/%y")
        return obj.return_date

    @admin.display(
        description=_("Nº de renovações"), ordering="renewals__count"
    )
    def n_renovations(self, obj):
        return obj.renewals__count

    def get_changeform_initial_data(self, request):
        from_qs = super().get_changeform_initial_data(request)
        defaults = {
            "date": timezone.now(),
            "duration": Period.get_default(),
        }

        defaults.update(from_qs)
        return defaults

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or (
            request.user.has_perm("loans.change_loan")
            and request.user.has_perm("loans.add_loan")
        ):
            return qs
        return qs.filter(user__user=request.user)
