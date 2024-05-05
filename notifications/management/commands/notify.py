from smtplib import SMTPException

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template import Context, Template
from django.utils import timezone
from django.utils.translation import gettext as _

from loans.models import Loan
from site_configuration.models import EmailConfiguration

from ...models import Notification, NotificationLog, Trigger

TriggerChoices = Trigger.TriggerChoices


User = get_user_model()


class Command(BaseCommand):
    help = "Import books from csv"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.querysets = {}
        self.mailconf = EmailConfiguration.get_solo()

    def html2text(self, html):
        return BeautifulSoup(html, "lxml").get_text()

    def get_recipient_list(self, user):
        return [
            user.email,
            *user.additional_emails.filter(
                receive_notifications=True
            ).values_list("email", flat=True),
        ]

    def get_context(self, loan):
        return Context(
            {
                "book": loan.specimen.book,
                "name": f"{loan.user.first_name} {loan.user.last_name}",
                "signature": self.mailconf.signature,
                "due": loan.due.strftime("%d/%m/%y"),
                "late_days": (timezone.now() - loan.due).days,
            }
        )

    def send(self, loan, notification):
        context = self.get_context(loan)
        message = Template(notification.message).render(context)
        subject = Template(notification.subject).render(context)

        # docs.djangoproject.com/en/5.0/topics/email/#preventing-header-injection
        subject = subject.replace("\n", " ")

        recipient_list = self.get_recipient_list(loan.user)
        send_mail(
            subject,
            self.html2text(message),
            # recipient_list=recipient_list,
            recipient_list=["joaoseckler@gmail.com"],
            html_message=message,
            fail_silently=False,
            auth_user=self.mailconf.username,
            auth_password=self.mailconf.password,
            from_email=self.mailconf.from_email,
        )

    def notify(self, notification, trigger):
        log = NotificationLog.objects.filter(notification=notification)
        n = notification.n_parameter

        for loan in trigger.get_queryset(self.querysets, n, log):
            try:
                self.send(loan, notification)
                log = NotificationLog(loan=loan, notification=notification)
                log.save()
            except SMTPException:
                self.stderr.write(
                    _("Não consegui enviar email para %(user)s")
                    % {"user": loan.user.profile}
                )

    def handle(self, *args, **options):
        if not self.mailconf.activated:
            self.stdout.write(
                self.style.WARNING(_("Email is not activated. Ignoring..."))
            )
            return

        self.querysets = {
            "late": Loan.objects.filter(late=True),
            "running": Loan.objects.filter(late=False, returned=False),
        }

        for notification in Notification.objects.all():
            for trigger in notification.triggers.all():
                self.notify(notification, TriggerChoices(trigger.ttype))
