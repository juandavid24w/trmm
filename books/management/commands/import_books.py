import re

import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.utils import timezone
from isbnlib import canonical, ean13

from ... import isbn
from ...models import Book, Classification, Location, Specimen
from ...validators import validate_isbn

User = get_user_model()
csv_file = settings.BASE_DIR / "more_books.csv"
USE_CSV_CODE = False


mandatory_fields = [
    "busca",
    "titulo",
    "editora",
    "autor",
]
fillable_fields = [
    "titulo",
    "autor",
    "editora",
]


def is_valid_isbn(val):
    if pd.isnull(val):
        return False
    try:
        validate_isbn(str(val))
    except ValidationError:
        return False
    return True


def dict_to_row(d):
    return {
        "titulo": d["title"],
        "autor": d["author"],
        "editora": d["publisher"],
    }

def get_publisher(raw):
    if pd.isnull(raw):
        return None
    return re.sub(r"[-,\d\s\.]*$", "", raw).title()

def get_author_names(raw):
    names = raw.split(";")[0]
    names = re.sub(r"[-,\d\s\.]*$", "", names)
    if "," in names:
        names = " ".join(reversed(names.split(",")))

    names = re.sub(r"[,.\d]", "", names)
    names = [name.strip() for name in names.split()]
    return [name + "." if len(name) == 1 else name for name in names]


def get_code(raw):
    if not USE_CSV_CODE or pd.isnull(raw):
        return None
    words = raw.split()
    return next(word for word in words if re.search(r"\d+", word))

class Command(BaseCommand):
    help = "Import books from csv"

    def fill_incomplete(self, row):
        if any(pd.isnull(row[f]) for f in fillable_fields):
            self.stdout.write(
                f"    Attempting to fetch data for {row['isbn']}..."
            )
            data, _ = isbn.search(str(row["isbn"]), split_author=False)
            if data:
                for field, value in dict_to_row(data).items():
                    if pd.isnull(row[field]):
                        row[field] = value

        is_complete = all(
            not pd.isnull(row[f]) and row[f].strip() for f in mandatory_fields
        )
        return row, is_complete

    def handle(self, *args, **options):
        df = pd.read_csv(csv_file)
        df["valid_isbn"] = df["isbn"].apply(is_valid_isbn)
        incomplete = []
        queryset = Book.objects.all()

        if not queryset.exists():
            existing_isbns = set()
            existing_titles = set()
        else:
            existing_isbns, existing_titles = map(
                set,
                zip(
                    *Book.objects.all().values_list("canonical_isbn", "title")
                ),
            )

        n = len(df.index)
        for i, row in df.iterrows():
            self.stdout.write(f"{i}/{n}")
            if not pd.isnull(row["isbn"]) and not row["valid_isbn"]:
                self.stdout.write(f"    Invalid ISBN: {row['isbn']}")
                incomplete.append(row)
                continue

            if pd.isnull(row["isbn"]) and pd.isnull(row["titulo"]):
                self.stdout.write(f"    Insuficient data!")
                incomplete.append(row)
                continue

            if (
                pd.isnull(row["isbn"]) and row["titulo"] in existing_titles
            ) or (
                not pd.isnull(row["isbn"])
                and ean13(canonical(row["isbn"])) in existing_isbns
            ):
                self.stdout.write(f"    {row['isbn']} already exists.")
                continue

            row, is_complete = self.fill_incomplete(row)
            if not is_complete:
                self.stdout.write(f"    Insuficient data!")
                incomplete.append(row)
                continue

            title = row["titulo"].strip("/ ").strip()
            self.stdout.write(f"    Importing {title}...")

            location, _ = Location.objects.get_or_create(
                name=row["localizacao"].strip().title()
            )
            classification, _ = Classification.objects.get_or_create(
                abbreviation=row["busca"].strip().title(),
                location=location,
            )

            author_names = get_author_names(row["autor"])
            book = Book(
                isbn=(
                    None
                    if pd.isnull(row["isbn"]) or not row["isbn"]
                    else row["isbn"]
                ),
                title=title,
                author_first_names=" ".join(author_names[:-1]),
                author_last_name=author_names[-1],
                publisher=get_publisher(row["editora"]),
                classification=classification,
                creation_date=timezone.now(),
                last_modified=timezone.now(),
            )

            book.save()
            book_code = get_code(row["etiqueta"])
            existing_titles.add(book.title)
            if book.isbn:
                existing_isbns.add(ean13(canonical(book.isbn)))

            for i in range(
                1 if pd.isnull(row["exemplares"]) else int(row["exemplares"])
            ):
                sp = Specimen(book=book)

                if USE_CSV_CODE:
                    code = f"{book_code} Ex {i + 1}"
                    if code:
                        sp.code = code
                sp.save()

        incomplete = pd.DataFrame(incomplete)
        incomplete = incomplete[
            [
                "isbn",
                "busca",
                "titulo",
                "editora",
                "autor",
                "exemplares",
                "valid_isbn",
            ]
        ]

        incomplete["exemplares"] = (
            incomplete["exemplares"].fillna(0).astype(int)
        )
        incomplete["busca"] = incomplete["busca"].apply(
            lambda b: str(b).title()
        )
        incomplete = incomplete.sort_values(
            ["busca", "titulo", "autor", "editora"]
        )
        incomplete.to_csv("incomplete.csv")
