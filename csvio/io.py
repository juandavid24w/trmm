import csv
from io import StringIO, TextIOWrapper
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework_csv.parsers import CSVParser
from rest_framework_csv.renderers import CSVRenderer

from .registry import CSVIORegistry


def csv_export(key):
    reg = CSVIORegistry.get(key)

    serializer = reg.serializer(reg.model.objects.all(), many=True)
    try:
        context = {"header": serializer.data.keys()}
    except AttributeError:
        try:
            context = {"header": serializer.data[0].keys()}
        except AttributeError:
            context = {}

    return CSVRenderer().render(
        serializer.data,
        renderer_context=context,
    )


def unique(*args):
    seen = set()
    seen_add = seen.add
    return [x for x in args if not (x in seen or seen_add(x))]


def get_errors(request, obj, errors):

    error_stream = StringIO()
    errors = [
        {
            f"{f}_error": " - ".join(e.title() for e in err)
            for f, err in error.items()
        }
        for error in errors
    ]

    obj.file.open("r")
    encoding = request.encoding or "utf-8"
    dialect = csv.Sniffer().sniff(
        TextIOWrapper(obj.file, encoding=encoding).read(1024)
    )

    obj.file.open("r")
    reader = csv.DictReader(obj.file, dialect=dialect)

    error_fieldnames = unique(
        *reader.fieldnames,
        *(f"{f}_error" for f in reader.fieldnames),
        *{f for error in errors for f, _ in error.items()},
    )
    writer = csv.DictWriter(error_stream, fieldnames=error_fieldnames)
    writer.writeheader()

    for line, errs in zip(reader, errors):
        writer.writerow({**line, **errs})

    return error_stream


def csv_import(request, obj):
    if not obj.file:
        return

    stream = obj.file.open()
    reg = CSVIORegistry.get(obj.key)

    data = CSVParser().parse(stream)
    serializer = reg.serializer(data=data, many=True)

    if serializer.is_valid():
        try:
            with transaction.atomic():
                serializer.save()
        except Exception as e:
            raise ValidationError(
                _(
                    "Não foi possível realizar a importação dos "
                    "%(objects)s : %(error)s"
                )
                % {
                    "objects": reg.model._meta.verbose_name_plural,
                    "error": str(e),
                }
            ) from e
        obj.error_file.delete()
    else:
        error_file = get_errors(request, obj, serializer.errors)

        if not obj.error_file.name:
            obj.error_file.save(
                name=_("erros_%(name)s") % {"name": Path(obj.file.name).name},
                content=ContentFile(error_file.getvalue()),
            )
        else:
            obj.error_file.open("w")
            obj.error_file.write(error_file.getvalue())
            obj.error_file.flush()

        raise ValidationError(
            _(
                "Não foi possível realizar a importação dos %(objects)s. "
                "Confira o arquivo de erros para maiores detalhes."
            )
            % {"objects": reg.model._meta.verbose_name_plural}
        )
