from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from isbnlib import is_isbn10, is_isbn13


def validate_isbn(value):
    if not (is_isbn10(value) or is_isbn13(value)):
        raise ValidationError(
            _("%(value)s não é um ISBN válido"),
            params={"value": value},
        )
