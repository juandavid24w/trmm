from ddf import G
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from ..actions import mark_label_printed, remove_label_printed
from ..models import Book, Specimen


class BookActionTestCase(TestCase):
    def setUp(self):
        self.yes = G(Book, specimens=G(Specimen, n=2), n=5)
        self.no = G(Book, specimens=G(Specimen, n=3), n=5)

        self.rf = RequestFactory()

    def get_request(self):
        request = self.rf.get("")
        request.session = {}
        request._messages = FallbackStorage(request)

        return request

    def test_actions(self):
        for s in Specimen.objects.all():
            self.assertFalse(s.label_printed)

        mark_label_printed(
            None,
            self.get_request(),
            self.yes,
        )

        for s in Specimen.objects.filter(
            book__pk__in=[o.pk for o in self.yes]
        ):
            self.assertTrue(s.label_printed)

        for s in Specimen.objects.filter(
            book__pk__in=[o.pk for o in self.no]
        ):
            self.assertFalse(s.label_printed)

        remove_label_printed(
            None,
            self.get_request(),
            self.yes,
        )

        for s in Specimen.objects.all():
            self.assertFalse(s.label_printed)
