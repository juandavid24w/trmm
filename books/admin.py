from django.contrib import admin
from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from admin_buttons.admin import AdminButtonsMixin
from barcodes.admin import BarcodeSearchBoxMixin
from biblioteca.admin import public_site
from loans.util import loan_link
from profiles.admin import HiddenAdminMixin
from public_admin.admin import PublicModelAdminMixin

from .models import Book, Classification, Location, Specimen

mark_safe_lazy = lazy(mark_safe, str)


def custom_title_filter_factory(title):
    class Wrapper(admin.AllValuesFieldListFilter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title = title

    return Wrapper


class SpecimenAdmin(HiddenAdminMixin, admin.ModelAdmin):
    def change_view(self, request, object_id, *args, **kwargs):
        obj = get_object_or_404(Specimen, pk=object_id)

        return redirect(
            reverse("admin:books_book_change", args=(obj.book.pk,))
        )

    search_fields = [
        "book__isbn",
        "book__title",
        "book__author_last_name",
        "book__author_first_names",
        "book__publisher",
        "book__classification__name",
    ]


class SpecimenInline(admin.TabularInline):
    fields = ["number", "code", "loan", "available"]
    readonly_fields = ["number", "code", "loan", "available"]
    model = Specimen
    extra = 0

    def has_add_permission(self, *args, **kwargs):
        return False

    @admin.display(description=_("Fazer empréstimo"))
    def loan(self, obj):
        return loan_link({"specimen": obj.id})

    @admin.display(description=_("Disponível?"), boolean=True)
    def available(self, obj):
        return obj.available


class BookAdmin(AdminButtonsMixin, BarcodeSearchBoxMixin, admin.ModelAdmin):
    inlines = [SpecimenInline]
    fields = [
        "isbn",
        "title",
        "author_last_name",
        "author_first_names",
        "publisher",
        "classification",
        "creation_date",
        "last_modified",
        "units",
        "available",
    ]
    readonly_fields = ["units", "creation_date", "last_modified", "available"]
    search_fields = (
        "isbn",
        "title",
        "author_last_name",
        "author_first_names",
        "publisher",
        "classification__name",
    )
    list_display = (
        "title",
        "author",
        "publisher",
        "classification",
        "location",
        "units",
        "short_last_modified",
    )
    list_filter = (
        (
            "classification__name",
            custom_title_filter_factory(_("classificação")),
        ),
        (
            "classification__location__name",
            custom_title_filter_factory(_("localização")),
        ),
    )

    @admin.display(
        description=_("Localização"), ordering="classification__location"
    )
    def location(self, obj):
        return obj.classification.location

    @admin.display(description=_("Exemplares"), ordering="specimens__count")
    def units(self, obj):
        return obj.units()

    @admin.display(description=_("Autoria"), ordering="author")
    def author(self, obj):
        return obj.author

    @admin.display(
        description=_("Última modificação"), ordering="last_modified"
    )
    def short_last_modified(self, obj):
        return obj.last_modified.strftime("%d/%m/%y")

    @admin.display(description=_("Disponível"), boolean=True)
    def available(self, obj):
        return obj.available

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.annotate(models.Count("specimens"))
        return qs

    admin_buttons_config = [
        {
            "name": "_addspecimen",
            "method": "add_specimen",
            "label": _("Adicionar exemplares"),
            "condition": lambda req, ctx: req.user.has_perm(
                "books.add_specimen"
            ),
            "extra_html": mark_safe_lazy(
                '<input type="number" step=1 min=1 max=99 value=1 '
                + f"name=\"n_specimens\" aria-label=\"{_('Número de exemplares')}\">"
            ),
        }
    ]

    def add_specimen(self, request, obj):
        n = int(request.POST["n_specimens"])
        if obj:
            for _ in range(n):
                obj.specimens.create()

        return redirect(request.META["HTTP_REFERER"])


class ClassificationAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name", "location")


class LocationAdmin(admin.ModelAdmin):
    pass


class PublicBookAdmin(PublicModelAdminMixin, BookAdmin):
    pass


class PublicClassificationAdmin(PublicModelAdminMixin, ClassificationAdmin):
    pass


class PublicLocationAdmin(PublicModelAdminMixin, LocationAdmin):
    pass


admin.site.register(Specimen, SpecimenAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Classification, ClassificationAdmin)

public_site.register(Book, PublicBookAdmin)
public_site.register(Location, PublicLocationAdmin)
public_site.register(Classification, PublicClassificationAdmin)
