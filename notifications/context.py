from django.template import Context
from django.utils import timezone

from site_configuration.models import SiteConfiguration


def get_context(loan=None, mailconf=None):
    fmt = "%d/%m/%y"
    return Context(
        {
            "site_title": loan and SiteConfiguration.get_solo().site_title,
            "book": loan and loan.specimen.book,
            "author": loan and loan.specimen.book.author,
            "name": loan and f"{loan.user.first_name} {loan.user.last_name}",
            "signature": mailconf and mailconf.signature,
            "due": loan and loan.due.strftime(fmt),
            "return_date": loan
            and loan.return_date
            and loan.return_date.strftime(fmt),
            "loan_date": loan and loan.date.strftime(fmt),
            "late_days": loan and (timezone.now() - loan.due).days,
        }
    )
