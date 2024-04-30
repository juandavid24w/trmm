from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from fieldsets_with_inlines import FieldsetsInlineMixin

from loans.util import loan_link

from .models import Email, Profile

User = get_user_model()
admin.site.unregister(User)


class HiddenAdminMixin:  # pylint: disable=too-few-public-methods
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class EmailInline(admin.TabularInline):
    model = Email
    extra = 0


@admin.register(Profile)
class ProfileAdmin(HiddenAdminMixin, admin.ModelAdmin):
    search_fields = ["user__first_name", "user__last_name", "grade"]


class ProfileInline(admin.TabularInline):
    model = Profile
    can_delete = False


@admin.register(User)
class UserAdmin(FieldsetsInlineMixin, BaseUserAdmin):
    fieldsets_with_inlines = list(BaseUserAdmin.fieldsets)
    fieldsets_with_inlines[2:2] = [
        (_("Empréstimo"), {"fields": ("loan",), "classes": ["hide-label"]}),
        ProfileInline,
        EmailInline,
    ]
    readonly_fields = ["loan"]

    def loan(self, obj):
        return loan_link({"user": obj.profile.pk}, _("Fazer empréstimo"))

    class Media:
        css = {"all": ["profiles/style.css"]}
