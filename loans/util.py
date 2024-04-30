from django.http import QueryDict
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .apps import LoansConfig
from .models import Loan

mark_safe_lazy = lazy(mark_safe, str)


def loan_link(opts, text=_("Emprestar")):
    qd = QueryDict("", mutable=True)
    qd.update(opts)
    base = reverse(f"admin:{LoansConfig.name}_{Loan._meta.model_name}_add")
    href = f"{base}?{qd.urlencode()}"
    return mark_safe_lazy(f"<a href={href}>{text}</a>")
