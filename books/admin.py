from django.contrib import admin
from django.db import models
from django.utils.translation import gettext as _

from .models import Book, Classification, Location, Specimen


class SpecimenInline(admin.StackedInline):
    model = Specimen
    extra = 0


def custom_title_filter_factory(title):
    class Wrapper(admin.AllValuesFieldListFilter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title = title

    return Wrapper


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    inlines = [SpecimenInline]
    readonly_fields = ["code"]
    search_fields = (
        "title",
        "author",
        "publisher",
        "classification__name",
        "code",
    )
    list_display = (
        "title",
        "author",
        "publisher",
        "classification",
        "location",
        "units",
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

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.annotate(models.Count("specimens"))
        return qs


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name", "location")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass
