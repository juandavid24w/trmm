import re
import time
import urllib.parse

from django import forms
from django.contrib import admin, messages
from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from isbnlib import canonical, clean, ean13, get_isbnlike
from unidecode import unidecode

from admin_buttons.admin import AdminButtonsMixin
from alter_field_action.actions import alter_field_action
from barcodes.admin import BarcodeSearchBoxMixin
from biblioteca.admin import public_site
from default_object.admin import DefaultObjectAdminMixin
from labels.models import LabelPageConfiguration, LabelPrint
from loans.util import loan_link
from profiles.admin import HiddenAdminMixin
from public_admin.admin import PublicModelAdminMixin

from . import isbn
from .models import Book, Classification, Collection, Location, Specimen
from .widgets import ISBNSearchInput

mark_safe_lazy = lazy(mark_safe, str)


def custom_title_filter_factory(title):
    class Wrapper(admin.AllValuesFieldListFilter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title = title

    return Wrapper


class UnaccentSearchMixin:
    def get_search_results(self, request, queryset, search_term):
        qs, has_dups = super().get_search_results(
            request, queryset, search_term
        )

        if search_term:
            if get_isbnlike(search_term, level="strict"):
                isbn_field = self.canonical_isbn_field
                isbn_search = ean13(canonical(clean(search_term)))
                qs |= self.model.objects.filter(**{isbn_field: isbn_search})

            request.search_unaccent = True
            unaccent_qs, unaccent_dups = super().get_search_results(
                request, queryset, unidecode(search_term)
            )
            request.search_unaccent = False

            qs |= unaccent_qs
            has_dups = has_dups or unaccent_dups

        return qs, has_dups

    def get_search_fields(self, request):
        if getattr(request, "search_unaccent", False):
            return self.unaccent_search_fields
        return super().get_search_fields(request)


class SpecimenIdSearchMixin:
    def get_search_results(self, request, queryset, search_term):
        qs, has_dups = super().get_search_results(
            request, queryset, search_term
        )

        if re.match(r"\d+", search_term):
            request.search_specimen_id = True
            new_qs, new_has_dups = super().get_search_results(
                request, queryset, str(int(search_term, base=10))
            )
            request.search_specimen_id = False

            qs |= new_qs
            has_dups = has_dups or new_has_dups

        return qs, has_dups

    def get_search_fields(self, request):
        if getattr(request, "search_specimen_id", False):
            return [self.specimen_id_field]
        return super().get_search_fields(request)


class SpecimenAdmin(
    SpecimenIdSearchMixin,
    UnaccentSearchMixin,
    HiddenAdminMixin,
    admin.ModelAdmin,
):
    canonical_isbn_field = "book__canonical_isbn"
    unaccent_search_fields = ("book__unaccent_title", "book__unaccent_author")
    specimen_id_field = "id"

    def change_view(
        self, request, object_id, form_url="", extra_context=None
    ):
        obj = get_object_or_404(Specimen, pk=object_id)

        return redirect("admin:books_book_change", args=(obj.book.pk,))

    search_fields = [
        "id",
        "book__isbn",
        "book__title",
        "book__author_last_name",
        "book__author_first_names",
        "book__publisher",
        "book__classification__name",
        "book__classification__abbreviation",
        "book__code",
    ]


class SpecimenInline(admin.TabularInline):
    model = Specimen
    fields = ["number", "loan", "available"]
    readonly_fields = ["number", "loan", "available"]
    extra = 0

    def has_add_permission(self, *args, **kwargs):
        return False

    @admin.display(description=_("Fazer empréstimo"))
    def loan(self, obj):
        return loan_link({"specimen": obj.id})

    @admin.display(description=_("Disponível?"), boolean=True)
    def available(self, obj):
        return obj.available


class BookAdminForm(forms.ModelForm):
    isbn_search_submit_name = "_isbnsearch"

    class Meta:
        model = Book
        widgets = {
            "isbn": ISBNSearchInput(),
        }
        fields = "__all__"


class BookAdmin(
    SpecimenIdSearchMixin,
    UnaccentSearchMixin,
    AdminButtonsMixin,
    BarcodeSearchBoxMixin,
    admin.ModelAdmin,
):

    form = BookAdminForm
    inlines = [SpecimenInline]
    fields = [
        "isbn",
        "title",
        "author_last_name",
        "author_first_names",
        "publisher",
        "classification",
        "collection",
        "code",
        "creation_date",
        "last_modified",
        "units",
        "available",
    ]
    readonly_fields = [
        "units",
        "creation_date",
        "last_modified",
        "available",
        "code",
    ]
    search_fields = (
        "isbn",
        "title",
        "author_last_name",
        "author_first_names",
        "publisher",
        "classification__name",
        "classification__abbreviation",
        "code",
        "specimens__id",
    )
    unaccent_search_fields = ("unaccent_author", "unaccent_title")
    canonical_isbn_field = "canonical_isbn"
    list_display = (
        "title",
        "author",
        "publisher",
        "classification",
        "location",
        "units",
        "short_last_modified",
    )
    ordering = ["-last_modified"]
    list_filter = (
        (
            "classification__abbreviation",
            custom_title_filter_factory(_("classificação")),
        ),
        (
            "classification__location__name",
            custom_title_filter_factory(_("localização")),
        ),
        (
            "collection__name",
            custom_title_filter_factory(_("acervo")),
        ),
    )
    actions = [
        "make_labels",
        alter_field_action(Book, "classification"),
        alter_field_action(Book, "collection"),
    ]
    specimen_id_field = "specimens__id"

    @admin.display(
        description=_("Localização"), ordering="classification__location"
    )
    def location(self, obj):
        return obj.classification.location.color_icon()

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

    @admin.action(description=_("Criar etiquetas"))
    def make_labels(self, request, queryset):
        if not request.user.has_perm(
            "labels.add_labelprint"
        ) or not request.user.has_perm("labels.add_labelprint"):
            messages.error(
                request,
                _("Usuário não tem permissão de criação de etiquetas"),
            )
            return None

        specimens = Specimen.objects.filter(book__in=queryset)
        configuration = LabelPageConfiguration.get_default()

        if not configuration:
            messages.error(
                request,
                _(
                    "Deve haver ao menos uma configuração de página de "
                    "etiquetas para se criar um arquivo de etiquetas."
                ),
            )
            return None

        obj = LabelPrint(configuration=configuration)

        obj.save()
        obj.specimens.add(*specimens)
        obj.save()  # Save again to generate pdf file

        url = reverse("admin:labels_labelprint_change", args=(obj.pk,))

        return redirect(url)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.annotate(models.Count("specimens"))
        return qs

    admin_buttons_config = [
        {
            "name": "_addspecimen",
            "method": "add_specimen",
            "label": _("Adicionar exemplares"),
            "condition": lambda req, ctx: (
                req.user.has_perm("books.add_specimen")
                and not re.search(r"add/?$", req.path)
            ),
            "extra_html": mark_safe_lazy(
                '<input type="number" step=1 min=1 max=99 value=1 '
                + f"name=\"n_specimens\" aria-label=\"{_('Número de exemplares')}\">"
            ),
        }
    ]

    def get_inline_instances(self, request, obj=None):
        ii = super().get_inline_instances(request, obj)

        if obj is None:
            return [i for i in ii if not isinstance(i, SpecimenInline)]

        return ii

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["help_texts"] = {
                "units": _(
                    "Salve o livro primeiro, depois adicione exemplares"
                )
            }
        else:
            kwargs["widgets"] = {}
        return super().get_form(request, obj, **kwargs)

    def add_specimen(self, request, obj):
        n = int(request.POST["n_specimens"])
        if obj:
            for _ in range(n):
                obj.specimens.create()

        return redirect(request.META["HTTP_REFERER"])

    def add_view(self, request, form_url="", extra_context=None):
        if ISBNSearchInput.isbn_search_submit_name in request.POST:
            isbn_value = request.POST["isbn"]
            results, msgs = isbn.search(isbn_value)
            href = reverse("admin:books_book_add")

            if not results:
                for msg in msgs:
                    messages.error(request, msg)
                results = {"isbn": isbn_value}
            else:
                for msg in msgs:
                    messages.success(request, msg)

            get_params = urllib.parse.urlencode(results)
            return redirect(f"{href}?{get_params}")

        return super().add_view(request, form_url, extra_context)

    def get_actions(self, request):
        actions = super().get_actions(request)

        if not request.user.has_perm(
            "labels.add_labelprint"
        ) or not request.user.has_perm("labels.change_labelprint"):
            del actions["make_labels"]

        return actions


class ClassificationAdmin(admin.ModelAdmin):
    list_display = ("__str__", "abbreviation", "location", "location_color")

    @admin.display(description=_("Cor da localização"))
    def location_color(self, obj):
        return obj.location.color_icon()

class LocationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "color_icon"]

    @admin.display(description=_("Cor"))
    def color_icon(self, obj):
        return obj.color_icon()


class CollectionAdmin(DefaultObjectAdminMixin, admin.ModelAdmin):
    pass


class PublicBookAdmin(PublicModelAdminMixin, BookAdmin):
    pass


class PublicClassificationAdmin(PublicModelAdminMixin, ClassificationAdmin):
    pass


class PublicLocationAdmin(PublicModelAdminMixin, LocationAdmin):
    pass


class PublicCollectionAdmin(PublicModelAdminMixin, CollectionAdmin):
    pass


admin.site.register(Specimen, SpecimenAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Classification, ClassificationAdmin)
admin.site.register(Collection, CollectionAdmin)

public_site.register(Book, PublicBookAdmin)
public_site.register(Location, PublicLocationAdmin)
public_site.register(Classification, PublicClassificationAdmin)
public_site.register(Collection, PublicCollectionAdmin)
