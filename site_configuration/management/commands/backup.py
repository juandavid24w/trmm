from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from ...admin import BackupAdmin, background_dump
from ...models import Backup


class Command(BaseCommand):
    help = "Make backup of the state of this site"

    def handle(self, *args, **kwargs):
        name = BackupAdmin.get_available_name(
            _("%(date)s_backup_automatico%(n)s")
        )
        backup = Backup.objects.create(name=name)
        background_dump(backup.pk)

        self.stdout.write(self.style.SUCCESS(_("Backup criado com sucesso")))
