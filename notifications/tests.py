from datetime import timedelta
from io import StringIO
from random import choice, randint, sample, shuffle
from unittest.mock import Mock

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.management import call_command
from django.db.models import F
from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.utils.translation import gettext as _

from books.models import Specimen
from books.tests.test_catalog import create_test_catalog
from loans.admin import LoanAdmin
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
        self.period.renewals.create(description="ren1", days=15, order=2)
        self.period.renewals.create(description="ren2", days=15, order=3)
        self.out = StringIO()
        self.rf = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            "admin",
            "admin@example.com",
            "admin",
        )

    def test_not_activated(self):
        call_command("notify", stdout=self.out)
        self.assertIn(_("Ignorando"), self.out.getvalue())

    def mk_loan(self, date=timezone.now(), save=True, renewals=0):
        assert save or not renewals

        loan = Loan(
            specimen=self.specimens.pop(),
            period=self.period,
            user=choice(self.users),
            date=date,
        )

        if save:
            loan.save()

        for i in range(renewals):
            loan.renewals.create(
                description="ren.",
                days=15,
                period=self.period,
                order=i + 1,
            )

        return loan

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
            for __ in range(randint(1, ns - 3)):
                no.append(self.mk_loan(infm - timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            for __ in range(randint(1, ns - 1)):
                no.append(self.mk_loan(maxm + timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            if n > 1:
                for __ in range(ns):
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
            for __ in range(randint(1, ns - 3)):
                no.append(self.mk_loan(lim + timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            for __ in range(ns):
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
            for __ in range(randint(1, ns - 3)):
                no.append(self.mk_loan(lim + timedelta(days=randint(1, 10))))

            ns = len(self.specimens)
            for __ in range(ns):
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
        loan_admin = LoanAdmin(model=Loan, admin_site=AdminSite())
        n = 3

        for __ in range(n):
            loan_admin.save_model(
                obj=self.mk_loan(),
                request=None,
                form=Mock(initial={"return_date": None}),
                change=None,
            )
        self.assertEqual(len(mail.outbox), 0)

        Loan.objects.all().update(return_date=timezone.now())
        self.assertEqual(len(mail.outbox), 0)

        trigger = TriggerChoices.LOAN_RECEIPT
        Notification.objects.create(
            name=f"notification_{trigger}",
            subject=f"subject {trigger}",
            message=f"<p>message {trigger}</p>",
            n_parameter=n,
            trigger=trigger,
        )

        for __ in range(n):
            loan_admin.save_model(
                obj=self.mk_loan(),
                request=None,
                form=Mock(initial={"return_date": None}),
                change=None,
            )
        self.assertEqual(len(mail.outbox), n)

        Loan.objects.all().update(date=F("date") - timedelta(days=3))
        for loan in Loan.objects.all():
            loan_admin.save_model(
                obj=loan,
                request=None,
                form=Mock(initial={"return_date": loan.return_date}),
                change=True,
            )

        self.assertEqual(
            len(mail.outbox),
            n,
            msg=_(
                "Nenhum email deveria ser enviado ao trocar a data do "
                "empréstimo"
            ),
        )

    def test_send_notification_return_receipt(self):
        loan_admin = LoanAdmin(model=Loan, admin_site=AdminSite())
        n = 3

        for __ in range(n):
            loan_admin.save_model(
                obj=self.mk_loan(), request=None, form=None, change=None
            )
        self.assertEqual(len(mail.outbox), 0)

        Loan.objects.all().update(return_date=timezone.now())
        self.assertEqual(len(mail.outbox), 0)

        Loan.objects.all().delete()

        trigger = TriggerChoices.RETURN_RECEIPT
        Notification.objects.create(
            name=f"notification_{trigger}",
            subject=f"subject {trigger}",
            message=f"<p>message {trigger}</p>",
            n_parameter=n,
            trigger=trigger,
        )

        for __ in range(n):
            loan_admin.save_model(
                obj=self.mk_loan(),
                request=None,
                form=Mock(initial={"return_date": None}),
                change=None,
            )
        self.assertEqual(len(mail.outbox), 0)

        for loan in Loan.objects.all():
            prev_rd = loan.return_date
            loan.return_date = (
                loan.return_date - timedelta(days=3)
                if loan.return_date
                else timezone.now()
            )
            loan_admin.save_model(
                obj=loan,
                request=None,
                form=Mock(initial={"return_date": prev_rd}),
                change=True,
            )
        self.assertEqual(len(mail.outbox), n)

        for loan in Loan.objects.all():
            prev_rd = loan.return_date
            loan.return_date = (
                loan.return_date - timedelta(days=3)
                if loan.return_date
                else timezone.now()
            )
            loan_admin.save_model(
                obj=loan,
                request=None,
                form=Mock(initial={"return_date": prev_rd}),
                change=True,
            )

        self.assertEqual(
            len(mail.outbox),
            n,
            msg=_(
                "Nenhum email deveria ser enviado ao trocar a data do "
                "empréstimo"
            ),
        )

        Loan.objects.all().update(
            return_date=F("return_date") - timedelta(days=3)
        )
        for loan in Loan.objects.all():
            prev_rd = loan.return_date
            loan.return_date = (
                loan.return_date - timedelta(days=3)
                if loan.return_date
                else timezone.now()
            )
            loan_admin.save_model(
                obj=loan,
                request=None,
                form=Mock(initial={"return_date": prev_rd}),
                change=True,
            )

        self.assertEqual(
            len(mail.outbox),
            n,
            msg=_(
                "Nenhum email deveria ser enviado ao trocar a data de "
                "devolução depois de já devolvido"
            ),
        )

    def get_request(self):
        request = self.rf.get(
            path="",
            HTTP_REFERER="admin:login",
        )
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        request.user = self.admin_user
        return request

    @staticmethod
    def getmsg(request):
        return str(next(iter(get_messages(request))))

    def test_send_notification_renewal_receipt(self):
        loan_admin = LoanAdmin(model=Loan, admin_site=AdminSite())
        n = 3
        error_msg = _("Não foi possível renovar")

        for __ in range(n):
            loan = self.mk_loan()
            loan_admin.save_model(
                obj=loan, request=None, form=None, change=None
            )
            loan = Loan.objects.get(pk=loan.pk)
            request = self.get_request()
            loan_admin.renew_view(request, loan)
            self.assertNotIn(error_msg, self.getmsg(request))

        self.assertEqual(len(mail.outbox), 0)
        Loan.objects.all().delete()

        trigger = TriggerChoices.RENEWAL_RECEIPT
        Notification.objects.create(
            name=f"notification_{trigger}",
            subject=f"subject {trigger}",
            message=f"<p>message {trigger}</p>",
            n_parameter=n,
            trigger=trigger,
        )

        for __ in range(n):
            loan = self.mk_loan()
            loan_admin.save_model(
                obj=loan,
                request=None,
                form=Mock(initial={"return_date": None}),
                change=None,
            )
            loan = Loan.objects.get(pk=loan.pk)
            request = self.get_request()
            loan_admin.renew_view(request, loan)
            self.assertNotIn(error_msg, self.getmsg(request))
        self.assertEqual(len(mail.outbox), n)

        for loan in Loan.objects.all():
            loan = Loan.objects.get(pk=loan.pk)
            request = self.get_request()
            loan_admin.renew_view(request, loan)
            self.assertIn(error_msg, self.getmsg(request))
            days = sum(loan.renewals.all().values_list("days", flat=True))
            loan.date = loan.date - timedelta(days=days)
            loan.save()
            request = self.get_request()
            loan_admin.renew_view(request, loan)
            self.assertNotIn(error_msg, self.getmsg(request))
        self.assertEqual(len(mail.outbox), 2 * n)

        mail.outbox = []
        for loan in Loan.objects.all():
            prev_rd = loan.return_date
            loan.return_date = (
                loan.return_date - timedelta(days=3)
                if loan.return_date
                else timezone.now()
            )
            loan_admin.save_model(
                obj=loan,
                request=None,
                form=Mock(initial={"return_date": prev_rd}),
                change=True,
            )

        self.assertEqual(
            len(mail.outbox),
            0,
            msg=_(
                "Nenhum email deveria ser enviado ao trocar a data do "
                "empréstimo"
            ),
        )

        Loan.objects.all().update(
            return_date=F("return_date") - timedelta(days=3)
        )
        for loan in Loan.objects.all():
            prev_rd = loan.return_date
            loan.return_date = (
                loan.return_date - timedelta(days=3)
                if loan.return_date
                else timezone.now()
            )
            loan_admin.save_model(
                obj=loan,
                request=None,
                form=Mock(initial={"return_date": prev_rd}),
                change=True,
            )

        self.assertEqual(
            len(mail.outbox),
            0,
            msg=_(
                "Nenhum email deveria ser enviado ao trocar a data de "
                "devolução depois de já devolvido"
            ),
        )
