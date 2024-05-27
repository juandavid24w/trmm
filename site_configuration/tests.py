import tarfile
from io import StringIO
from pathlib import Path

from ddf import G
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from .admin import background_dump, restore_from_pk
from .backups import (
    BACKUP_PATH,
    DB_FILENAME,
    MEDIA_FILENAME,
    VERSION_FILENAME,
)
from .models import Backup, SiteConfiguration


class BackupTestCase(TestCase):
    def _test_media_dump(self, fileobj):
        with tarfile.open(fileobj=fileobj) as tar:
            self.assertTrue(
                all(
                    m.path.startswith(settings.MEDIA_ROOT.name)
                    for m in tar.getmembers()
                )
            )
            self.assertFalse(
                any(
                    str(m.path)
                    == str(Path(settings.MEDIA_ROOT.name) / BACKUP_PATH)
                    for m in tar.getmembers()
                )
            )

    def _test_dump(self, backup):
        name = backup.dump.name
        path = backup.dump.path
        self.assertTrue(Path(path).is_file())
        self.assertTrue(name)
        self.assertTrue(name.endswith(".tar"))

        with tarfile.open(path) as tar:
            self.assertEqual(
                {MEDIA_FILENAME, DB_FILENAME, VERSION_FILENAME},
                set(tar.getnames()),
            )
            self._test_media_dump(
                tar.extractfile(tar.getmember(MEDIA_FILENAME))
            )

        backup.delete()
        self.assertFalse(Path(path).is_file())

    def test_dump(self):
        backup = G(Backup, dump=None)
        background_dump(backup.pk)
        backup.refresh_from_db()

        self._test_dump(backup)

    def test_management_command(self):
        self.assertFalse(Backup.objects.all())
        call_command("backup", stdout=StringIO())
        self.assertTrue(Backup.objects.all())
        backup = Backup.objects.first()

        self._test_dump(backup)

    def test_restore(self):
        n_backup_files = len(
            list(Path(settings.MEDIA_ROOT / BACKUP_PATH).iterdir())
        )

        conf = SiteConfiguration.get_solo()
        conf.site_title = "Before dump"
        conf.save()

        test_path = settings.MEDIA_ROOT / "tmp.txt"
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("xpto")

        self.assertTrue(test_path.is_file())

        backup = G(Backup, dump=None)
        background_dump(backup.pk)

        remain = G(Backup, name="must remain", dump=None)
        background_dump(remain.pk)

        conf.site_title = "After dump"
        conf.save()

        restore_from_pk(backup.pk)

        conf = SiteConfiguration.get_solo()
        self.assertEqual(conf.site_title, "Before dump")

        self.assertTrue(test_path.is_file())
        test_path.unlink()
        self.assertFalse(test_path.is_file())

        self.assertTrue(Backup.objects.all())
        remained = Backup.objects.get(name="must remain")
        self.assertTrue(remained)
        self.assertTrue(remained.dump.name)
        self.assertTrue(remained.dump.storage.exists(remained.dump.name))

        Backup.objects.all().delete()
        self.assertEqual(
            n_backup_files,
            len(list(Path(settings.MEDIA_ROOT / BACKUP_PATH).iterdir())),
        )
