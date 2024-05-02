from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
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

    def change_view(self, request, object_id, *args, **kwargs):
        obj = get_object_or_404(Profile, pk=object_id)

        return redirect(
            reverse("admin:auth_user_change", args=(obj.user.pk,))
        )


class ProfileInline(admin.TabularInline):
    model = Profile
    can_delete = False


def change_grade(queryset, up):
    for user in queryset:
        try:
            grade = Profile.Grade(user.profile.grade)
            user.profile.grade = grade.next() if up else grade.prev()
            user.profile.save()
        except ValueError:
            user.profile.grade = None
        except ObjectDoesNotExist:
            pass


@admin.action(description=_("Passar para a próxima série"))
def make_advance_grade(_modeladmin, _request, queryset):
    change_grade(queryset, up=True)


@admin.action(description=_("Passar para a série anterior"))
def make_return_grade(_modeladmin, _request, queryset):
    change_grade(queryset, up=False)


@admin.register(User)
class UserAdmin(FieldsetsInlineMixin, BaseUserAdmin):
    list_display = list(BaseUserAdmin.list_display)
    list_display.insert(-1, "profile_grade")
    fieldsets_with_inlines = list(BaseUserAdmin.fieldsets)
    fieldsets_with_inlines[2:2] = [
        (_("Empréstimo"), {"fields": ("loan",), "classes": ["hide-label"]}),
        ProfileInline,
        EmailInline,
    ]
    readonly_fields = ["loan"]
    actions = [*BaseUserAdmin.actions, make_advance_grade, make_return_grade]

    def loan(self, obj):
        return loan_link({"user": obj.profile.pk}, _("Fazer empréstimo"))

    @admin.display(description=_("Série"))
    def profile_grade(self, obj):
        return obj.profile.grade

    class Media:
        css = {"all": ["profiles/style.css"]}
