from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from books.models import Book, Classification, Location
from books.serializers import (
    BookHyperlinkedSerializer,
    ClassificationHyperlinkedSerializer,
    LocationHyperlinkedSerializer,
)
from profiles.serializers import UserSerializer

User = get_user_model()


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookHyperlinkedSerializer
    permission_classes = [AllowAny]


class ClassificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Classification.objects.all()
    serializer_class = ClassificationHyperlinkedSerializer
    permission_classes = [AllowAny]


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationHyperlinkedSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
