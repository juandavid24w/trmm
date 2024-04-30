from django.contrib import admin
from django.db import models
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from barcodes.admin import BarcodeSearchBoxAdmin
from loans.util import loan_link
from profiles.admin import HiddenAdminMixin

from .models import Book, Classification, Location, Specimen


def custom_title_filter_factory(title):
    class Wrapper(admin.AllValuesFieldListFilter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title = title

    return Wrapper


@admin.register(Specimen)
class SpecimenAdmin(HiddenAdminMixin, admin.ModelAdmin):
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


@admin.register(Book)
class BookAdmin(BarcodeSearchBoxAdmin):
    change_form_template = "books/change_form.html"

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
    ]
    readonly_fields = ["units", "creation_date", "last_modified"]
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

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.annotate(models.Count("specimens"))
        return qs

    def add_specimen(self, request, obj, n):
        if obj:
            for _ in range(n):
                obj.specimens.create()

        return redirect(request.META["HTTP_REFERER"])

    def response_change(self, request, obj, *args, **kwargs):
        if "_addspecimen" in request.POST:
            n = int(request.POST["n_specimens"])
            return self.add_specimen(request, obj, n)

        return super().response_change(request, obj, *args, **kwargs)

    class Media:
        css = {"all": ["books/custom_submit_row.css"]}


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name", "location")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass
