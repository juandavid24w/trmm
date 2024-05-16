from io import StringIO
from pathlib import Path
from shutil import make_archive, rmtree, unpack_archive
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from django.conf import settings
from django.core.management import call_command
from django.core.management.commands import dumpdata, loaddata
from django.db import connections

BASE_PATH = Path("backups")


class BackupError(ValueError):
    pass


def reopen_connections():
    for key in settings.DATABASES:
        connections[key] = connections.create_connection(key)


def get_filenames(name, db=True):
    return (
        BASE_PATH
        / f"{name}_{'db' if db else 'media'}.{'zip' if db else 'tar'}"
    )


def dump_db(obj):
    filename = get_filenames(obj.name, db=True)
    json_fn = settings.MEDIA_ROOT / filename.with_suffix(".json")

    error_stream = StringIO()
    with open(json_fn, "w", encoding="utf-8") as f:
        call_command(
            dumpdata.Command(),
            verbosity=0,
            stderr=error_stream,
            stdout=f,
            natural_foreign=True,
            natural_primary=True,
        )
    error = error_stream.read()
    if error:
        raise BackupError(error.split("\n"))

    try:
        with ZipFile(settings.MEDIA_ROOT / filename, "w") as zipfile:
            zipfile.write(json_fn, json_fn.name)
    except OSError as e:
        raise BackupError(str(error).split("\n")) from e

    return filename


def dump_media(obj):
    filename = get_filenames(obj.name, db=False)
    try:
        make_archive(
            settings.MEDIA_ROOT / filename.with_suffix(""),
            "tar",
            settings.MEDIA_ROOT,
        )
    except OSError as e:
        raise BackupError(e) from e

    return filename


def restore_from_obj(obj):
    if obj.do_db_dump and obj.db_dump.name:
        with ZipFile(settings.MEDIA_ROOT / obj.db_dump.name, "r") as zipfile:
            name = zipfile.namelist()[0]
            name = zipfile.extract(name)

        stream = StringIO()
        call_command(
            loaddata.Command(),
            name,
            verbosity=0,
            stderr=stream,
        )
        error = stream.read()
        if error:
            raise BackupError(error.split("\n"))

    if obj.do_media_dump and obj.media_dump.name:
        with TemporaryDirectory(dir=settings.BASE_DIR) as tmpdir:
            tmpmedia = settings.MEDIA_ROOT.rename(tmpdir)
            unpack_archive(
                tmpmedia / obj.media_dump.name, settings.MEDIA_ROOT, "tar"
            )
            rmtree(tmpmedia)
