import re

import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Book, Classification, Location
from ...validators import validate_isbn

User = get_user_model()
csv_file = settings.BASE_DIR / "all_books.csv"


def get_author_names(raw):
    names = raw.split(";")[0]
    names = re.sub(r"[-,\d\s\.]*$", "", names)
    if "," in names:
        names = " ".join(reversed(names.split(",")))

    names = re.sub("[,.\d]", "", names)
    names = [name.strip() for name in names.split()]
    return [name + "." if len(name) == 1 else name for name in names]


class Command(BaseCommand):
    help = "Import books from csv"

    def handle(self, *args, **options):
        df = pd.read_csv(csv_file)
        df = df[df["etiqueta_impressa"] == "sim"]
        df = df[pd.notnull(df["isbn"])]

        for _, row in df.iterrows():
            try:
                validate_isbn(row["isbn"])
            except ValidationError:
                continue
            title = row["titulo"].strip("/ ").strip()
            self.stdout.write(f"Importing {title}...")

            location, _ = Location.objects.get_or_create(
                name=row["localizacao"].strip().title()
            )
            classification, _ = Classification.objects.get_or_create(
                abbreviation=row["busca"].strip().title(),
                location=location,
            )

            author_names = get_author_names(row["autor"])

            book = Book(
                isbn=row["isbn"],
                title=title,
                author_first_names=" ".join(author_names[:-1]),
                author_last_name=author_names[-1],
                publisher=row["editora"],
                classification=classification,
                creation_date=timezone.now(),
                last_modified=timezone.now(),
            )

            book.save()

            for _ in range(
                1 if pd.isnull(row["exemplares"]) else int(row["exemplares"])
            ):
                book.specimens.create()
