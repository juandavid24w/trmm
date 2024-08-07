"""
URL configuration for biblioteca project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from django.views.static import serve

from site_configuration.views import PasswordResetView

from .admin import public_site

urlpatterns = [
    *(
        [
            path("__debug__/", include("debug_toolbar.urls")),
            re_path(
                "^media/(?P<path>.*)$",
                serve,
                {
                    "document_root": settings.MEDIA_ROOT,
                },
            ),
        ]
        if settings.DEBUG
        else []
    ),
    path(
        "admin/password_reset/",
        PasswordResetView.as_view(
            extra_context={"site_header": admin.site.site_header}
        ),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            extra_context={"site_header": admin.site.site_header}
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            extra_context={"site_header": admin.site.site_header}
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            extra_context={"site_header": admin.site.site_header}
        ),
        name="password_reset_complete",
    ),
    path("accounts/login/", RedirectView.as_view(url="/admin/")),
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("api/", include("api.urls")),
    path("", public_site.urls),
]
