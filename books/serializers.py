from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Book, Classification, Location


class LocationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Location
        fields = ["url", "name", "color"]


class ClassificationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Classification
        fields = ["url", "name", "abbreviation", "location"]


class BookSerializer(serializers.HyperlinkedModelSerializer):
    location = serializers.HyperlinkedRelatedField(
        source="classification.location",
        view_name="location-detail",
        read_only=True,
    )
    units = serializers.IntegerField(
        required=False,
        write_only=True,
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["units"] = instance.units()

        return data

    def create(self, validated_data):
        units = validated_data.pop("units")

        book = super().create(validated_data)

        for _ in range(units):
            book.specimens.create()

        return book

    class Meta:
        model = Book
        fields = [
            "url",
            "id",
            "isbn",
            "title",
            "author_first_names",
            "author_last_name",
            "author",
            "publisher",
            "classification",
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
