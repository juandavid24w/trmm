from datetime import timedelta
from io import StringIO
from random import choice, randint, sample, shuffle

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.db.models import F
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext as _

from books.models import Specimen
from books.tests.test_catalog import create_test_catalog
from loans.models import Loan, Period
from profiles.tests import create_test_users
from site_configuration.models import EmailConfiguration

from .mail import DynamicSMPTEmailBackend, send_notification
from .models import Notification, NotificationLog

User = get_user_model()
TriggerChoices = Notification.TriggerChoices


def example_mailconf():
    return EmailConfiguration.objects.create(
        activated=False,
        host="smtp.example.com",
        port="587",
        username="admin@example.com",
        password="admin",
        from_email="admin@example.com",
        signature="<p>Goodby, world!</p>",
    )


class EmailBackendTestCase(TestCase):
    def setUp(self):
        self.mailconf = example_mailconf()

    def test_backend(self):
        backend = DynamicSMPTEmailBackend()
        for field in (
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
        ):
            self.assertEqual(
                str(getattr(backend, field)),
                str(getattr(self.mailconf, field)),
            )


class NotificationTestCase(TestCase):
    def setUp(self):
        self.mailconf = example_mailconf()
        create_test_catalog()
        create_test_users()

        self.users = list(User.objects.all())
        self.specimens = list(Specimen.objects.all())
        shuffle(self.specimens)
        self.period = Period.get_default()
        self.out = StringIO()

    def test_not_activated(self):
        call_command("notify", stdout=self.out)
        self.assertIn(_("Ignorando"), self.out.getvalue())

    def mk_loan(self, date=timezone.now()):
        return Loan.objects.create(
            specimen=self.specimens.pop(),
            period=self.period,
            user=choice(self.users),
            date=date,
        )

    def test_send_notification(self):
        self.mk_loan()
        loan = Loan.objects.first()

        notification = Notification.objects.create(
            name="Notification",
            subject="Testing the subject",
            message="<p>Testing the message</p>{{ signature }}",
            trigger=1,
            n_parameter=5,
        )
        send_notification(loan, notification)

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn(self.mailconf.signature, sent.body)
        self.assertIn(notification.subject, sent.subject)

        emails = {
            *loan.user.additional_emails.all().values_list(
                "email", flat=True
            ),
            loan.user.email,
        }
        self.assertEqual(emails, set(sent.recipients()))

    def test_send_notification_due_in_n(self):
        self.mailconf.activated = True
        self.mailconf.save()

        for n in (1, *sample(range(1, 45), 4)):
            trigger = TriggerChoices.DUE_IN_N
            Notification.objects.create(
                name=f"notification_{trigger}",
                subject=f"subject {trigger}",
                message=f"<p>message {trigger}</p>",
                n_parameter=n,
                trigger=trigger,
            )
            period = self.period

            no = []
            yes = []

            infm = timezone.now() - timedelta(days=period.days)
            maxm = timezone.now() + timedelta(days=n - period.days)

            no.append(self.mk_loan(infm))
            no.append(self.mk_loan(maxm + timedelta(seconds=5)))
            yes.append(self.mk_loan(infm + timedelta(seconds=5)))
            yes.append(self.mk_loan(maxm))

            ns = len(self.specimens)
            for _ in range(randint(1, ns - 3)):
                no.append(self.mk_loan(infm - timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            for _ in range(randint(1, ns - 1)):
                no.append(self.mk_loan(maxm + timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            if n > 1:
                for _ in range(ns):
                    yes.append(
                        self.mk_loan(infm + timedelta(randint(1, n - 1)))
                    )

            self.assertFalse(mail.outbox)
            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), len(yes))

            mail.outbox = []
            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), 0)

            self.assertEqual(
                set(Loan.objects.filter(notificationlog__isnull=False)),
                set(yes),
            )
            self.assertEqual(
                set(Loan.objects.filter(notificationlog__isnull=True)),
                set(no),
            )

            self.users = list(User.objects.all())
            self.specimens = list(Specimen.objects.all())
            shuffle(self.specimens)

            Loan.objects.all().delete()
            NotificationLog.objects.all().delete()
            Notification.objects.all().delete()
            mail.outbox = []

    def test_send_notification_late_after_n(self):
        self.mailconf.activated = True
        self.mailconf.save()

        for n in (1, *sample(range(1, 45), 4)):
            trigger = TriggerChoices.LATE_AFTER_N
            Notification.objects.create(
                name=f"notification_{trigger}",
                subject=f"subject {trigger}",
                message=f"<p>message {trigger}</p>",
                n_parameter=n,
                trigger=trigger,
            )
            period = self.period

            no = []
            yes = []

            lim = timezone.now() + timedelta(days=-period.days - n)

            no.append(self.mk_loan(lim + timedelta(seconds=5)))
            yes.append(self.mk_loan(lim))

            ns = len(self.specimens)
            for _ in range(randint(1, ns - 3)):
                no.append(self.mk_loan(lim + timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            for _ in range(ns):
                yes.append(self.mk_loan(lim - timedelta(days=randint(1, 10))))

            self.assertFalse(mail.outbox)
            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), len(yes))

            self.assertEqual(
                set(Loan.objects.filter(notificationlog__isnull=False)),
                set(yes),
            )
            self.assertEqual(
                set(Loan.objects.filter(notificationlog__isnull=True)),
                set(no),
            )

            mail.outbox = []
            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), 0)

            self.users = list(User.objects.all())
            self.specimens = list(Specimen.objects.all())
            shuffle(self.specimens)

            Loan.objects.all().delete()
            NotificationLog.objects.all().delete()
            Notification.objects.all().delete()
            mail.outbox = []

    def test_send_notification_late_after_each_n(self):
        self.mailconf.activated = True
        self.mailconf.save()

        for n in (1, *sample(range(1, 45), 4)):
            trigger = TriggerChoices.LATE_AFTER_EACH_N
            Notification.objects.create(
                name=f"notification_{trigger}",
                subject=f"subject {trigger}",
                message=f"<p>message {trigger}</p>",
                n_parameter=n,
                trigger=trigger,
            )
            period = self.period

            no = []
            yes = []

            lim = timezone.now() + timedelta(days=-period.days - n)

            no.append(self.mk_loan(lim + timedelta(seconds=5)))
            yes.append(self.mk_loan(lim))

            ns = len(self.specimens)
            for _ in range(randint(1, ns - 3)):
                no.append(self.mk_loan(lim + timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            for _ in range(ns):
                yes.append(self.mk_loan(lim - timedelta(days=randint(1, 10))))

            self.assertFalse(mail.outbox)
            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), len(yes))

            self.assertEqual(
                set(Loan.objects.filter(notificationlog__isnull=False)),
                set(yes),
            )
            self.assertEqual(
                set(Loan.objects.filter(notificationlog__isnull=True)),
                set(no),
            )

            mail.outbox = []
            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), 0)

            Loan.objects.filter(pk__in=[o.pk for o in yes]).update(
                date=F("date") - timedelta(days=n)
            )
            NotificationLog.objects.all().update(
                created=F("created") - timedelta(days=n)
            )

            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), len(yes))

            mail.outbox = []
            call_command("notify", stdout=self.out)
            self.assertEqual(len(mail.outbox), 0)

            self.users = list(User.objects.all())
            self.specimens = list(Specimen.objects.all())
            shuffle(self.specimens)

            Loan.objects.all().delete()
            NotificationLog.objects.all().delete()
            Notification.objects.all().delete()
            mail.outbox = []

    def test_send_notification_loan_receipt(self):
        loan = self.mk_loan()
        loan = self.mk_loan()
        loan = self.mk_loan()
        self.assertEqual(len(mail.outbox), 3)
