from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_isbn(value):
    if len(value) not in (10, 13) or any(not c.isdigit() for c in value):
        raise ValidationError(
            _(
                "%(value)s não é um ISBN válido (deve ter 10 ou 13 dígitos núméricos)"
            ),
            params={"value": value},
        )
