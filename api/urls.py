from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"books", views.BookViewSet)
router.register(r"classifications", views.ClassificationViewSet)
router.register(r"locations", views.LocationViewSet)
router.register(r"collections", views.CollectionViewSet)
router.register(r"users", views.UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
