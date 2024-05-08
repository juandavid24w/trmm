from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from ...admin import BackupAdmin
from ...models import Backup


class Command(BaseCommand):
    help = "Make backup of the state of this site"

    def handle(self, *args, **kwargs):
        name = BackupAdmin.get_available_name(
            _("%(date)s_backup_automatico%(n)s")
        )
        Backup(
            name=name,
            do_db_dump=True,
            do_media_dump=True,
        ).save()

        self.stdout.write(self.style.SUCCESS(_("Backup criado com sucesso")))
