from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Notification, NotificationLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "trigger", "n_parameter"]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["user", "book", "notification", "created"]
    fields = ["user", "book", "notification", "loan", "created"]
    readonly_fields = fields
    ordering = ["-created"]

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_add_permission(self, *args, **kwargs):
        return False

    @admin.display(description=_("Usuário"), ordering="loan__user")
    def user(self, obj):
        return obj.loan.user.profile

    @admin.display(description=_("Livro"), ordering="loan__specimen__book")
    def book(self, obj):
        return obj.loan.specimen.book
