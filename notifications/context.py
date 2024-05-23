from django.template import Context
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime

from site_configuration.models import SiteConfiguration


def get_context(loan=None, mailconf=None):
    fmt = "%d/%m/%y"
    values = {
        "site_title": loan and SiteConfiguration.get_solo().site_title,
        "book": loan and loan.specimen.book,
        "author": loan and loan.specimen.book.author,
        "name": loan and f"{loan.user.first_name} {loan.user.last_name}",
        "signature": mailconf and mailconf.signature,
        "due": loan and localtime(loan.due).strftime(fmt),
        "return_date": loan
        and loan.return_date
        and localtime(loan.return_date).strftime(fmt),
        "loan_date": loan and loan.date.strftime(fmt),
        "late_days": loan and (timezone.now() - localtime(loan.due)).days,
    }

    return Context({k: mark_safe(v) for k, v in values.items()})
