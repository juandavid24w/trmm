from datetime import datetime, time, timedelta
from random import choice

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import localtime

from books.models import Book, Classification, Collection, Location, Specimen
from books.tests.test_catalog import create_test_catalog
from profiles.tests import create_test_users
from site_configuration.models import SiteConfiguration

from .models import Loan, Period

User = get_user_model()

def create_test_period():
    default_period = Period.get_default()
    default_period.renewals.create(
        description="renewal 1",
        days=10,
        order=1,
    )
    default_period.renewals.create(
        description="renewal 2",
        days=15,
        order=2,
    )
    default_period.order = 3
    default_period.save()

    return default_period

class EmptyDBTestCase(TestCase):
    def test_create_default_period(self):
        self.assertIsNotNone(Period.get_default())


class LoanAndPeriodTestCase(TestCase):
    def setUp(self):
        create_test_catalog()
        create_test_users()

        self.default_period = create_test_period()

    def get_specimen_user(self):
        for user in User.objects.all():
            for book in Book.objects.all():
                for specimen in book.specimens.all():
                    yield specimen, user

    def fuzz_periods(self, yes_period, no_period, field, random):
        """Add some extra values to the periods' m2m fields"""
        logop = yes_period.logical_operator

        for rf, rm, _, rex in random:
            if rf != field:
                if logop == Period.LogicalOperatorChoices.OR:
                    if instances := rm.objects.all():
                        getattr(yes_period, rf).add(choice(instances))
                    if exclude := rm.objects.exclude(
                        pk__in=[o.pk for o in rex]
                    ):
                        getattr(no_period, rf).add(choice(exclude))

                else:
                    if exclude := rm.objects.exclude(
                        pk__in=[o.pk for o in rex]
                    ):
                        getattr(no_period, rf).add(choice(exclude))
                    if include := rm.objects.filter(
                        pk__in=[o.pk for o in rex]
                    ):
                        getattr(yes_period, rf).add(choice(include))

    def test_select_period_single(self):
        for specimen, user in self.get_specimen_user():
            groups = user.groups.all()
            compare = (
                (
                    "collections",
                    Collection,
                    specimen.book.collection,
                    [specimen.book.collection],
                ),
                (
                    "locations",
                    Location,
                    specimen.book.classification.location,
                    [specimen.book.classification.location],
                ),
                (
                    "classifications",
                    Classification,
                    specimen.book.classification,
                    [specimen.book.classification],
                ),
                (
                    "groups",
                    Group,
                    choice(groups) if groups else None,
                    groups,
                ),
                ("users", User, user, [user]),
                ("books", Book, specimen.book, [specimen.book]),
                ("specimens", Specimen, specimen, [specimen]),
            )

            random = [choice(compare), choice(compare), choice(compare)]

            for logop in Period.LogicalOperatorChoices:
                for field, model, obj, exclude in compare:
                    no_obj = model.objects.exclude(
                        pk__in=[o.pk for o in exclude]
                    ).first()

                    no_period = Period.objects.create(
                        description="No collection",
                        logical_operator=logop,
                    )
                    getattr(no_period, field).add(no_obj)

                    yes_period = Period.objects.create(
                        description="Yes collection",
                        logical_operator=logop,
                    )

                    self.fuzz_periods(yes_period, no_period, field, random)

                    if obj:
                        getattr(yes_period, field).add(obj)
                        self.assertEqual(
                            Period.select_period(specimen, user), yes_period
                        )
                    else:
                        self.assertIn(
                            Period.select_period(specimen, user),
                            [self.default_period, yes_period],
                        )
                    yes_period.delete()
                    no_period.delete()

    def test_create_default(self):
        self.assertIsNotNone(Period.get_default())

    def test_loan(self):
        user = choice(User.objects.all())
        specimen = choice(Specimen.objects.all())

        loan = Loan(user=user, specimen=specimen)
        loan.save()
        self.assertEqual(loan.period, self.default_period)
        self.assertIsNone(loan.renew())
        self.assertEqual(
            loan.renewals.first(), self.default_period.renewals.first()
        )
        self.assertIsNotNone(loan.renew())
        loan.date -= timedelta(days=loan.period.days)
        self.assertIsNone(loan.renew())
        self.assertIsNone(loan.unrenew())
        self.assertIsNone(loan.unrenew())
        self.assertIsNotNone(loan.unrenew())

        loan.delete()

        specimen = choice(
            Specimen.objects.filter(book__collection__isnull=False)
        )
        period = Period(description="with collection")
        period.save()
        period.collections.add(specimen.book.collection)

        loan = Loan(user=user, specimen=specimen)
        loan.save()

        self.assertEqual(loan.period, period)
        self.assertIsNotNone(loan.renew())
        loan.delete()


class LoanDueTestCase(TestCase):
    def setUp(self):
        create_test_catalog()
        create_test_users()

        self.specimens = list(Specimen.objects.all())
        self.users = list(User.objects.all())
        self.conf = SiteConfiguration().get_solo()
        self.period = create_test_period()

    def mk_loan(self, date=timezone.now(), renewals=0):
        loan = Loan(
            specimen=self.specimens.pop(),
            period=self.period,
            user=choice(self.users),
            date=date,
        )
        loan.save()

        for i in range(renewals):
            loan.renewals.create(
                description="ren.",
                days=15,
                period=self.period,
                order=i + 1,
            )

        loan = Loan.objects.get(pk=loan.pk)
        return loan

    def test_loan_due(self):
        for day in range(7):
            for hour in range(7):
                loan = self.mk_loan(
                    date=timezone.make_aware(
                        datetime.combine(
                            timezone.now().date(), time(2 + 3 * hour)
                        )
                        + timedelta(days=day)
                    )
                )
                loan = Loan.objects.get(pk=loan.pk)
                self.assertIn(
                    (localtime(loan.due).isoweekday() - 1) % 7 + 2,
                    self.conf.get_working_days(),
                    msg="Loans should be due to working days only",
                )
                self.assertEqual(
                    localtime(loan.due).time(),
                    self.conf.ending_hour,
                    msg="All loans should be due when the library closes",
                )
                self.assertGreaterEqual(
                    loan.due, loan.exact_due, msg="Due must be >= exact due"
                )
            self.specimens = list(Specimen.objects.all())
            self.users = list(User.objects.all())
            Loan.objects.all().delete()
