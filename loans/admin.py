from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin, messages
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from admin_buttons.admin import AdminButtonsMixin
from barcodes.admin import BarcodeSearchBoxMixin

from .filters import LoanStatusFilter
from .models import Loan, Period, Renewal


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ["description", "days"]


@admin.register(Renewal)
class RenewalAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["description", "days"]


@admin.action(description=_("Marcar devolução"))
def make_returned(_modeladmin, _request, queryset):
    queryset.filter(return_date__isnull=True).update(
        return_date=timezone.now()
    )


@admin.register(Loan)
class LoanAdmin(AdminButtonsMixin, BarcodeSearchBoxMixin, admin.ModelAdmin):
    autocomplete_fields = ["specimen", "user"]
    ordering = ["-date"]
    readonly_fields = ["renewals", "due"]
    list_display = [
        "user",
        "title",
        "author",
        "isbn",
        "short_date",
        "short_due",
        "short_return_date",
        "n_renovations",
        "late",
    ]
    list_filter = [
        LoanStatusFilter,
        "date",
        ("user", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "user__first_name",
        "user__last_name",
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
        return obj.due.strftime("%d/%m/%Y, %H:%M")

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

    @admin.display(description=_("atrasado"), boolean=True)
    def late(self, obj):
        return not obj.return_date and obj.due < timezone.now()

    def get_changeform_initial_data(self, request):
        from_qs = super().get_changeform_initial_data(request)
        period = Period.get_default()
        defaults = {
            "date": timezone.now(),
            **({"duration": period} if period else {}),
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
        return qs.filter(user=request.user)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "renew/<int:obj_or_id>",
                self.admin_site.admin_view(self.renew_view),
                name="loans_loan_renew",
            )
        ]
        return my_urls + urls

    def change_view(self, request, object_id, *args, form_url="", **kwargs):
        if not request.user.has_perm("loans.change_loan"):
            form_url = reverse("admin:loans_loan_renew", args=(object_id,))

        return super().change_view(
            request,
            object_id,
            *args,
            form_url=form_url,
            **kwargs,
        )

    def renew_view(self, request, obj_or_id):
        """renew_view can be called from two places:
        * coming from a user with change permission, it is called by
          admin_button's response_change (see admin_buttons_config). In
          this case, this view receives the object itself
        * Otherwise, a custom form_url (the form action) is set to the
          change form, which is associated with this view (see get_urls).
          In this case, this view receives the object's id
        """

        if isinstance(obj_or_id, int):
            obj = get_object_or_404(Loan, pk=obj_or_id)
        else:
            obj = obj_or_id

        message = _("Não foi possível renovar: %s")

        if (
            not request.user.has_perm("loans.change_loan")
            and request.user != obj.user
        ):
            messages.error(
                request,
                message % _("usuário não bate com usuário do empréstimo"),
            )
        elif obj.return_date:
            messages.error(request, message % _("exemplar já foi devolvido"))
        elif obj.due < timezone.now():
            messages.error(request, message % _("exemplar já está atrasado"))
        else:
            if msg := obj.renew():
                messages.error(request, message % msg)

        return redirect(request.META["HTTP_REFERER"])

    def unrenew_view(self, request, obj):
        message = _("Não foi possível remover renovação: %s")

        if not request.user.has_perm("loans.change_loan"):
            messages.error(
                request,
                message % _("usuário não tem permissão"),
            )
        else:
            if msg := obj.unrenew():
                messages.error(request, message % msg)

        return redirect(request.META["HTTP_REFERER"])

    admin_buttons_config = [
        {
            "name": "_renew",
            "label": _("Renovar"),
            "method": "renew_view",
        },
        {
            "name": "_unrenew",
            "label": _("Remover renovação"),
            "method": "unrenew_view",
            "condition": lambda req, ctx: req.user.has_perm(
                "loans.change_loan"
            ),
            "use_separator": False,
        },
    ]
