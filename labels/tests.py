from django.test import TestCase

from .models import LabelPageConfiguration


class LabelPageConfigurationTestCase(TestCase):
    def test_create_default_if_empty(self):
        self.assertIsNotNone(LabelPageConfiguration.get_default())
