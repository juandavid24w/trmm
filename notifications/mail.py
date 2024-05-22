from smtplib import SMTPException

from bs4 import BeautifulSoup
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.template import Template
from django.utils.translation import gettext as _

from loans.models import Loan
from site_configuration.models import EmailConfiguration

from .context import get_context
from .models import Notification, NotificationLog

TriggerChoices = Notification.TriggerChoices


class DynamicSMPTEmailBackend(EmailBackend):
    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        use_tls=None,
        fail_silently=False,
        use_ssl=None,
        timeout=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        **kwargs,
    ):
        conf = EmailConfiguration.get_solo()

        super().__init__(
            host=host or conf.host,
            port=port or conf.port,
            username=username or conf.username,
            password=password or conf.password,
            use_tls=use_tls or conf.use_tls,
            fail_silently=fail_silently,
            use_ssl=use_ssl or conf.use_ssl,
            timeout=timeout or conf.timeout,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            **kwargs,
        )


def html2text(html):
    return BeautifulSoup(html, "lxml").get_text()


def get_recipient_list(user):
    return [
        user.email,
        *user.additional_emails.filter(
            receive_notifications=True
        ).values_list("email", flat=True),
    ]


def send_notification(loan, notification):
    mailconf = EmailConfiguration.get_solo()
    context = get_context(loan, mailconf)
    message = Template(notification.message).render(context)
    subject = Template(notification.subject).render(context)

    # docs.djangoproject.com/en/5.0/topics/email/#preventing-header-injection
    subject = subject.replace("\n", " ")

    recipient_list = get_recipient_list(loan.user)
    send_mail(
        subject,
        html2text(message),
        # recipient_list=recipient_list,
        recipient_list=["joaoseckler@gmail.com"],
        html_message=message,
        fail_silently=False,
        auth_user=mailconf.username,
        auth_password=mailconf.password,
        from_email=mailconf.from_email,
    )
    NotificationLog.objects.create(loan=loan, notification=notification)


def notify(querysets, notification, trigger):
    n = notification.n_parameter
    log = NotificationLog.objects.filter(notification=notification)

    count = 0
    for loan in trigger.get_queryset(querysets, n, log):
        try:
            send_notification(loan, notification)
        except SMTPException as e:
            raise SMTPException(
                _("Não consegui enviar email para %(user)s")
                % {"user": loan.user.profile}
            ) from e
        count += 1

    return count


def notify_all():
    mailconf = EmailConfiguration.get_solo()

    if not mailconf.activated:
        return None

    querysets = {
        "late": Loan.objects.filter(late=True),
        "running": Loan.objects.filter(late=False, returned=False),
    }

    errors = []
    sucesses = 0
    for notification in Notification.objects.all():
        try:
            sucesses += notify(
                querysets,
                notification,
                TriggerChoices(notification.trigger),
            )
        except SMTPException as e:
            errors.append(e)

    if errors:
        raise ExceptionGroup(_("Alguns erros foram encontrados"), errors)

    return sucesses


def receipt(loan, trigger):
    loan = Loan.objects.get(pk=loan.pk) # Get manager's annotations
    notifications = Notification.objects.filter(trigger=trigger)

    for notification in notifications:
        send_notification(loan, notification)


def loan_receipt(loan):
    return receipt(loan, TriggerChoices.LOAN_RECEIPT)


def return_receipt(loan):
    return receipt(loan, TriggerChoices.RETURN_RECEIPT)


def renewal_receipt(loan):
    return receipt(loan, TriggerChoices.RENEWAL_RECEIPT)
