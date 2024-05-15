from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from isbnlib import ISBNLibException, meta

from .models import Book
from .validators import validate_isbn

book_fields = [field.name for field in Book._meta.get_fields()]


def lowercase_percentage(string):
    try:
        return sum(char.islower() for char in string) / sum(
            char.islower() or char.isupper() for char in string
        )
    except ZeroDivisionError:
        return 0


def is_str_list(l):
    return all(isinstance(el, str) for el in l)


def preferred(a, b):
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return max(a, b, key=len)
        if is_str_list(a) and is_str_list(b):
            return max(
                a,
                b,
                key=lambda lst: sum(lowercase_percentage(e) for e in lst),
            )
        return a

    if isinstance(a, str) and isinstance(b, str):
        return max(a, b, key=lowercase_percentage)

    return a


def get_isbn_data(isbn):
    sources = ["wiki", "goob", "openl"]

    data = {}
    error_count = 0

    for source in sources:
        try:
            for key, val in meta(isbn, source).items():
                if key not in data:
                    data[key] = val
                else:
                    data[key] = preferred(data[key], val)
        except ISBNLibException:
            error_count += 1

    if error_count == len(sources):
        raise ISBNLibException

    return data


def get_last_first(authors):
    first = []
    last = None

    for i, author in enumerate(authors):
        names = [name.title() for name in author.split()]
        if names:
            if i == 0:
                last = names.pop()
                if names:
                    first.append(" ".join(names))
            else:
                if len(names) > 1:
                    first.append(f"{names[-1]}, {' '.join(names[:-1])}")
                else:
                    first.append(names[-1])

    return last or "", "; ".join(first)


def fix_keys(values, split_author=True):
    new = {}
    for key, value in values.items():
        if key == "ISBN-13":
            new["isbn"] = value
        elif key == "Authors" and isinstance(value, list):
            if split_author:
                last, first = get_last_first(value)
                new["author_last_name"] = last
                new["author_first_names"] = first
            else:
                new["author"] = "; ".join(set(value))
        elif key.lower() in book_fields:
            new[key.lower()] = value
        else:
            new[key] = value

    return new


def search(isbn, split_author=True):
    try:
        validate_isbn(isbn)
    except ValidationError as e:
        return None, e.messages
    try:
        return (
            fix_keys(get_isbn_data(isbn), split_author),
            [_("Informações carregadas do ISBN corretamente")],
        )
    except ISBNLibException:
        return None, [_("Erro ao buscar informações do isbn... :(")]
