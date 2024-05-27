import tarfile
from io import BytesIO, StringIO
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import call_command
from django.core.management.commands import dumpdata, flush, loaddata
from django.utils.translation import gettext as _

BACKUP_PATH = Path("backups")
DB_FILENAME = "db.json"
MEDIA_FILENAME = "media.tar"
VERSION_FILENAME = "version.txt"


class BackupError(ValueError):
    pass

def get_commit():
    folder = settings.BASE_DIR / ".git"
    head = folder / "HEAD"
    with open(head, "r", encoding="utf-8") as f:
        ref = f.read()

    if ": " in ref:
        path = ref.split(": ")[1]
        with open(folder / path.strip(), "r", encoding="utf-8") as f:
            ref = f.read()

    return ref.strip()


def get_version(obj=None):
    if obj:
        with tarfile.open(fileobj=obj.dump.open()) as tar:
            version = tar.extractfile(tar.getmember(VERSION_FILENAME))
            return version.read().decode("utf-8")
    else:
        return get_commit()

def dump_db():
    error_stream = StringIO()
    output_stream = StringIO()
    call_command(
        dumpdata.Command(),
        verbosity=0,
        stderr=error_stream,
        stdout=output_stream,
        natural_foreign=True,
        natural_primary=True,
        exclude=["site_configuration.Backup"],
    )
    error = error_stream.getvalue()
    if error:
        raise BackupError(error.split("\n"))

    return BytesIO(output_stream.getvalue().encode("utf-8"))


def dump_media():
    output_stream = BytesIO()
    try:
        with tarfile.open(fileobj=output_stream, mode="w:gz") as tar:
            tar.add(
                settings.MEDIA_ROOT,
                arcname=settings.MEDIA_ROOT.name,
                filter=lambda x: (
                    None
                    if str(x.path)
                    == str(Path(settings.MEDIA_ROOT.name) / BACKUP_PATH)
                    else x
                ),
            )
    except OSError as e:
        raise BackupError(e) from e

    output_stream.seek(0)
    return output_stream


def dump():
    output_stream = BytesIO()
    data = (
        (DB_FILENAME, dump_db()),
        (MEDIA_FILENAME, dump_media()),
        (VERSION_FILENAME, BytesIO(get_commit().encode("utf-8"))),
    )

    with tarfile.open(fileobj=output_stream, mode="w:gz") as tar:
        for name, file in data:
            info = tarfile.TarInfo(name)
            info.size = len(file.getvalue())
            tar.addfile(info, file)

    return output_stream.getvalue()

def save_backups():
    backup_db_stream = StringIO()
    backup_media_stream = BytesIO()
    error_stream = StringIO()

    call_command(
        dumpdata.Command(),
        "site_configuration.Backup",
        verbosity=0,
        stderr=error_stream,
        stdout=backup_db_stream,
        natural_foreign=True,
        natural_primary=True,
    )
    error = error_stream.getvalue()
    if error:
        raise BackupError(error.split("\n"))

    with tarfile.open(fileobj=backup_media_stream, mode="w:gz") as tar:
        path = settings.MEDIA_ROOT / BACKUP_PATH
        tar.add(path, arcname=path.name)

    backup_media_stream.seek(0)
    return backup_db_stream, backup_media_stream


def restore_from_obj(obj):
    data = {
        DB_FILENAME: None,
        MEDIA_FILENAME: None,
        VERSION_FILENAME: None,
    }

    with tarfile.open(fileobj=obj.dump.open("rb")) as tar:
        for name in data:
            try:
                data[name] = BytesIO(
                    tar.extractfile(tar.getmember(name)).read()
                )
            except KeyError as e:
                raise BackupError(
                    _("Esperava encontrar %(name)s no arquivo de backup")
                    % {"name": name}
                ) from e

    if data[VERSION_FILENAME].getvalue().decode("utf-8") != get_commit():
        raise BackupError(
            _(
                "Versão do arquivo de backup não coincide com versão "
                "do sistema"
            )
        )

    backup_db, backup_media = save_backups()

    error_stream = StringIO()
    call_command(
        flush.Command(),
        verbosity=0,
        stderr=error_stream,
        interactive=False,
    )
    error = error_stream.getvalue()
    if error:
        raise BackupError(error.split("\n"))

    with TemporaryDirectory(dir=settings.BASE_DIR) as tmpdir:
        for content, mode in (
            (data[DB_FILENAME].getvalue(), "wb"),
            (backup_db.getvalue(), "w"),
        ):
            path = Path(tmpdir) / "tmp.json"
            with open(path, mode) as f:
                f.write(content)
            call_command(
                loaddata.Command(),
                path,
                verbosity=0,
                stderr=error_stream,
            )
            error = error_stream.getvalue()
            if error:
                raise BackupError(error.split("\n"))

    with (
        TemporaryDirectory(dir=settings.BASE_DIR) as tmpdir,
        tarfile.open(fileobj=data[MEDIA_FILENAME]) as tar,
    ):
        tmpmedia = settings.MEDIA_ROOT.rename(tmpdir)
        tar.extractall(path=settings.MEDIA_ROOT.parent)
        rmtree(tmpmedia)

    with tarfile.open(fileobj=backup_media) as tar:
        tar.extractall(path=settings.MEDIA_ROOT)
