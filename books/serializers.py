from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import csvio

from .isbn import search
from .models import Book, Classification, Collection, Location


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["name", "is_default"]

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["name", "color"]


class ClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classification
        fields = ["name", "abbreviation", "location"]


class BookSerializer(serializers.ModelSerializer):
    location = serializers.StringRelatedField(
        source="classification.location",
        read_only=True,
    )
    units = serializers.IntegerField(
        required=False,
        write_only=True,
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["units"] = instance.units()
        data["collection"] = Collection.objects.get(pk=data["collection"])

        return data

    def to_internal_value(self, data):
        if isinstance(data["collection"], str):
            name = data["collection"]
            try:
                data["collection"] = Collection.objects.get(name=name).pk
            except Collection.DoesNotExist as e:
                raise serializers.ValidationError(
                    {
                        "collection": [
                            _("Acervo inválido: %(name)s") % {"name": name}
                        ]
                    }
                ) from e

        return super().to_internal_value(data)

    def create(self, validated_data):
        units = validated_data.pop("units", 0)

        book = super().create(validated_data)

        for _ in range(units):
            book.specimens.create()

        return book

    class Meta:
        model = Book
        fields = [
            "id",
            "isbn",
            "title",
            "author_first_names",
            "author_last_name",
            "author",
            "publisher",
            "classification",
            "collection",
            "location",
            "code",
            "creation_date",
            "last_modified",
            "units",
            "available",
        ]
        read_only_fields = [
            "creation_date",
            "last_modified",
            "available",
            "code",
        ]
        write_only_fields = [
            "author_first_names",
            "author_last_name",
        ]


class ISBNSearchBookSerializer(BookSerializer):
    def to_internal_value(self, data):
        fields = ["title", "publisher", "author_last_name"]
        if (
            any(f not in data or not data[f] for f in fields)
            and "isbn" in data
            and data["isbn"]
        ):
            searched_data, _ = search(data["isbn"])
            for f in fields:
                if f not in data or not data[f]:
                    data[f] = searched_data.pop(f)
            data.update(searched_data)

        return super().to_internal_value(data)


class HyperlinkedMixin(serializers.HyperlinkedModelSerializer):
    def get_field_names(self, *args, **kwargs):
        return ["url", *super().get_field_names(*args, **kwargs)]


class CollectionHyperlinkedSerializer(
    CollectionSerializer,
    HyperlinkedMixin,
):
    pass

class LocationHyperlinkedSerializer(
    LocationSerializer,
    HyperlinkedMixin,
):
    pass


class ClassificationHyperlinkedSerializer(
    ClassificationSerializer,
    HyperlinkedMixin,
):
    pass


class BookHyperlinkedSerializer(
    BookSerializer,
    HyperlinkedMixin,
):
    location = serializers.HyperlinkedRelatedField(
        source="classification.location",
        view_name="location-detail",
        read_only=True,
    )


csvio.register(Book, BookSerializer)
csvio.register(
    Book,
    ISBNSearchBookSerializer,
    name="search",
    label=_("Livros (com busca por ISBN)"),
    use_with="import",
)
csvio.register(Collection, CollectionSerializer)
csvio.register(Location, LocationSerializer)
csvio.register(Classification, ClassificationSerializer)
