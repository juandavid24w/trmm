from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps

from .models import DefaultObjectMixin


@isolate_apps("default_object")
class DefaultObjectTestCase(TestCase):
    class TestModel(DefaultObjectMixin, models.Model):
        name = models.CharField(max_length=4)

        def __str__(self):
            return self.name

    class DefaultFieldsModel(DefaultObjectMixin, models.Model):
        name = models.CharField(max_length=4, default="zzzz")
        number = models.IntegerField(default=42)

        def __str__(self):
            return self.name

    class NoDefaultFieldsModel(DefaultObjectMixin, models.Model):
        name = models.CharField(max_length=4)
        number = models.IntegerField()

        def __str__(self):
            return self.name

    def setUp(self):
        self.TestModel.objects.create(name="def", is_default=True)
        self.TestModel.objects.create(name="aaaa")

    def test_field(self):
        obj = self.TestModel.objects.get(name="def")
        self.assertTrue(obj.is_default)

        obj = self.TestModel.objects.get(name="aaaa")
        self.assertFalse(obj.is_default)

    def test_get_default(self):
        self.assertEqual(self.TestModel.get_default().name, "def")

    def test_set_default(self):
        old = self.TestModel.objects.get(name="def")
        new = self.TestModel.objects.get(name="aaaa")

        new.is_default = True
        new.save()

        old = self.TestModel.objects.get(name="def")
        new = self.TestModel.objects.get(name="aaaa")

        self.assertFalse(old.is_default)
        self.assertTrue(new.is_default)

        self.assertEqual(new, self.TestModel.get_default())

    def test_create_default(self):
        obj = self.DefaultFieldsModel.get_default()
        self.assertEqual("zzzz", obj.name)
        self.assertEqual(42, obj.number)
        self.assertTrue(obj.is_default)

    def test_create_default_error(self):
        self.assertIsNone(self.NoDefaultFieldsModel.get_default())
