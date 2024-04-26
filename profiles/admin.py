from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from fieldsets_with_inlines import FieldsetsInlineMixin

from .models import Email, Profile

User = get_user_model()


class EmailInline(admin.TabularInline):
    model = Email


class ProfileInline(admin.TabularInline):
    model = Profile
    can_delete = False


class UserAdmin(FieldsetsInlineMixin, BaseUserAdmin):
    fieldsets_with_inlines = list(BaseUserAdmin.fieldsets)
    fieldsets_with_inlines[2:2] = [ProfileInline, EmailInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
