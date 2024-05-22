from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from fieldsets_with_inlines import FieldsetsInlineMixin
from hidden_admin.admin import HiddenAdminMixin
from loans.util import loan_link

from .models import Email, Profile

User = get_user_model()
admin.site.unregister(User)



class EmailInline(admin.TabularInline):
    model = Email
    extra = 0


@admin.register(Profile)
class ProfileAdmin(HiddenAdminMixin, admin.ModelAdmin):
    search_fields = ["user__first_name", "user__last_name", "grade"]

    redirect_related_field = {
        "change": "user",
        "add": "user",
        "delete": "user",
    }


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
    add_form_template = "admin/auth/user/add_form.html"

    list_display = [x for x in BaseUserAdmin.list_display if x != "is_staff"]
    list_display.insert(-1, "profile_grade")
    list_display.append("is_moderator")
    fieldsets_with_inlines = list(BaseUserAdmin.fieldsets)
    fieldsets_with_inlines[2:2] = [
        (_("Empréstimo"), {"fields": ("loan",), "classes": ["hide-label"]}),
        ProfileInline,
        EmailInline,
    ]
    readonly_fields = ["loan"]
    actions = [*BaseUserAdmin.actions, make_advance_grade, make_return_grade]

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return super(FieldsetsInlineMixin, self).get_inline_instances(
                request, obj
            )
        return super().get_inline_instances(request, obj)

    def get_fieldsets(self, request, obj=None, *args, **kwargs):
        if obj is None:
            return super(FieldsetsInlineMixin, self).get_fieldsets(
                request, obj, *args, **kwargs
            )

        return super().get_fieldsets(request, obj, *args, **kwargs)

    def loan(self, obj):
        return loan_link({"user": obj.profile.pk}, _("Fazer empréstimo"))

    @admin.display(description=_("Série"))
    def profile_grade(self, obj):
        return obj.profile.grade

    @admin.display(description=_("Moderador"), boolean=True)
    def is_moderator(self, obj):
        return obj.has_perm("loans.add_loan")

    class Media:
        css = {"all": ["profiles/style.css"]}
