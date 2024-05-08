import re
from smtplib import SMTPException

from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.admin.views.main import ChangeList
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions, action
from solo.admin import SingletonModelAdmin

from admin_buttons.admin import AdminButtonsMixin

from .backups import restore_from_obj
from .models import (
    Backup,
    DocumentationPage,
    EmailConfiguration,
    SiteConfiguration,
)

admin.site.register(SiteConfiguration, SingletonModelAdmin)


class DocumentationChangeList(ChangeList):
    def url_for_result(self, result):
        url = super().url_for_result(result)
        return f"{url}?detail=true"


@admin.register(DocumentationPage)
class DocumentationAdmin(
    DjangoObjectActions, SortableAdminMixin, admin.ModelAdmin
):
    change_form_template = "site_configuration/change_form.html"
    change_actions = ["to_edit_action", "to_detail_action"]

    @action(label=_("Editar"), description=_("Editar essa documentação"))
    def to_edit_action(self, request, obj):
        base = reverse(
            "admin:site_configuration_documentationpage_change",
            args=(obj.pk,),
        )
        return redirect(base)

    @action(
        label=_("Visualizar"), description=_("Visualizar essa documentação")
    )
    def to_detail_action(self, request, obj):
        base = reverse(
            "admin:site_configuration_documentationpage_change",
            args=(obj.pk,),
        )
        return redirect(f"{base}?detail=true")

    def get_change_actions(self, request, object_id=None, form_url=""):
        if request.GET.get("detail", False):
            return ["to_edit_action"]
        return ["to_detail_action"]

    def get_changelist(self, request, **kwargs):
        return DocumentationChangeList

    def has_change_permission(self, request, obj=None):
        if request.GET.get("detail", False):
            return False
        return super().has_change_permission(request, obj)

    class Media:
        css = {
            "all": ["site_configuration/style.css"],
        }


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(DjangoObjectActions, SingletonModelAdmin):
    change_actions = ["test_email"]

    @action(
        label=_("Testar email"),
        description=_(
            "Envie um email da conta configurada abaixo para o email "
            "cadastrado como remetente. Se algo der errado, nós "
            "avisaremos. Salve as configurações antes de testar."
        ),
    )
    def test_email(self, request, obj):
        host = request.get_host()
        try:
            send_mail(
                message=_(
                    "Enviamos esse email para verificar se ele está bem "
                    + "configurado na administração de %(host)s. "
                    + "Parece que sim!"
                )
                % {"host": host},
                from_email=obj.from_email,
                subject=_("[%(host)s] Teste de email") % {"host": host},
                recipient_list=[obj.from_email],
                fail_silently=False,
            )
        except SMTPException as e:
            messages.error(
                request,
                _("Email não está bem configurado: %s") % str(e),
            )
            return

        messages.success(
            request,
            _("Email está bem configurado! :)"),
        )


@admin.register(Backup)
class BackupAdmin(AdminButtonsMixin, DjangoObjectActions, admin.ModelAdmin):
    readonly_fields = ["created"]
    add_exclude = ["created", "db_dump", "media_dump"]
    upload_exclude = ["created", "do_db_dump", "do_media_dump"]
    list_display = [
        "__str__",
        "do_db_dump",
        "do_media_dump",
        "created",
        "restore",
    ]
    changelist_actions = ["upload"]

    @action(label=_("Upload"), description=_("Fazer upload de arquivos de backup"))
    def upload(self, request, obj):
        url = reverse("admin:site_configuration_backup_add")
        return HttpResponseRedirect(f"{url}?upload=true")

    def get_initial_name(self):
        names = Backup.objects.all().values_list("name", flat=True)
        date = timezone.now().strftime("%y.%m.%d")

        i = 0
        candidate = _("%(date)s_backup%(n)s")

        while (
            name := candidate % {"date": date, "n": f"_{i}" if i else ""}
        ) in names:
            i += 1

        return name

    def get_changeform_initial_data(self, request):
        from_qs = super().get_changeform_initial_data(request)
        defaults = {"name": self.get_initial_name()}

        defaults.update(from_qs)
        return defaults

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        exclude = []

        if obj is None:
            try:
                if "upload" in request.GET:
                    exclude = self.upload_exclude
                else:
                    exclude = self.add_exclude
            except AttributeError:
                pass

            return [
                field for field in fields if field not in exclude
            ]

        return fields

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "restore/<object_id>",
                self.admin_site.admin_view(self.restore_view),
                name="site_configuration_backup_restore",
            )
        ]
        return my_urls + urls

    def change_view(
        self, request, object_id, form_url="", extra_context=None
    ):
        form_url = reverse(
            "admin:site_configuration_backup_restore", args=(object_id,)
        )

        return super().change_view(
            request, object_id, form_url, extra_context
        )

    def save_model(self, request, obj, form, change):
        if "upload" in request.GET:
            obj.do_db_dump = bool(obj.db_dump.name)
            obj.do_media_dump = bool(obj.media_dump.name)

        super().save_model(request, obj, form, change)

    @admin.display(description=" ")
    def restore(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                "admin:site_configuration_backup_restore", args=(obj.pk,)
            ),
            _("Restaurar"),
        )

    def restore_view(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))

        if request.method == "POST" and "_restore" in request.POST:
            messages.success(request, _("Restauração realizada com sucesso"))
            restore_from_obj(obj)

            return redirect("admin:site_configuration_backup_changelist")
        if request.method == "POST" and "_restorecancel" in request.POST:
            url = reverse(
                "admin:site_configuration_backup_change", args=(object_id,)
            )
            return redirect(url)

        context = dict(
            self.admin_site.each_context(request),
            title=_("Restaurar %s") % obj.name,
        )
        return render(
            request, "site_configuration/restore.html", context=context
        )

    admin_buttons_config = [
        {
            "name": "_restoreconfirm",
            "method": "restore_view",
            "label": _("Restaurar esse backup"),
            "condition": lambda req, ctx: not re.search(r"add/?$", req.path),
        }
    ]

    class Media:
        css = {
            "all": [
                "site_configuration/backup.css",
            ]
        }
