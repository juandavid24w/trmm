from django.test import TestCase

from .models import Period, Renewal


class PeriodTestCase(TestCase):
    def test_create_default_if_empty(self):
        self.assertIsNotNone(Period.get_default())


class RenewalTestCase(TestCase):
    def test_create_default_if_empty(self):
        self.assertIsNotNone(Renewal.get_default())
