from smtplib import SMTPException
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from ...mail import notify_all


class Command(BaseCommand):
    help = "Import books from csv"

    def handle(self, *args, **options):
        try:
            ret = notify_all()
        except SMTPException as e:
            raise CommandError(f"Erro de envio de email: {e}") from e

        if ret is None:
            self.stdout.write(
                self.style.WARNING(_("Email não está ativado. Ignorando..."))
            )
            return

        if not ret:
            self.stdout.write(_("Não há notificações a serem enviadas"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                ngettext(
                    "Uma notificação foi enviada com sucesso",
                    "%(count)d notificações foram enviadas com sucesso",
                    ret,
                )
                % {"count": ret}
            )
        )
