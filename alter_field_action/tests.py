import re
from random import choice, randint, sample, shuffle

from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.db import models
from django.test import RequestFactory, TestCase
from django.test.utils import isolate_apps, override_settings
from django.urls import path, reverse

from .actions import alter_field_action

User = get_user_model()


@isolate_apps("alter_field_action")
class AlterFieldActionTestCase(TestCase):
    class RelatedTestModel(models.Model):
        name = models.CharField(max_length=4, default="rrrr")

        def __str__(self):
            return self.name

    class TestModel(models.Model):
        name = models.CharField(max_length=5, default="xxxx")
        number = models.IntegerField(default=0)
        rel = models.ForeignKey("RelatedTestModel", on_delete=models.CASCADE)
        o2o = models.OneToOneField(
            "RelatedTestModel",
            on_delete=models.CASCADE,
            related_name="testmodel_o2o_set",
        )
        m2m = models.ManyToManyField(
            "RelatedTestModel", related_name="testmodel_m2m_set"
        )

        def __str__(self):
            return self.name

    class TestModelAdmin(admin.ModelAdmin):
        pass

    TestModelAdmin.actions = [
        alter_field_action(TestModel, "name"),
        alter_field_action(TestModel, "number"),
        alter_field_action(
            TestModel,
            "rel",
            forms.ModelChoiceField(queryset=RelatedTestModel.objects.all()),
        ),
        alter_field_action(
            TestModel,
            "m2m",
        ),
    ]

    site = admin.AdminSite(name="admin_custom_urls")
    site.register(TestModel, TestModelAdmin)

    def setUp(self):
        rels = []

        for i in range(8):
            rels.append(self.RelatedTestModel.objects.create(name=f"rel{i}"))

        for _ in range(4):
            o2o = self.RelatedTestModel.objects.filter(
                testmodel_o2o_set__isnull=True
            )
            obj = self.TestModel(
                name=f"test{i}",
                rel=choice(rels),
                o2o=o2o and choice(o2o),
            )
            obj.save()
            for i in range(randint(0, 3)):
                obj.m2m.add(choice(rels))

        self.rf = RequestFactory()
        self.admin = self.site.get_model_admin(self.TestModel)
        self.admin_user = User.objects.create_superuser(
            "admin",
            "admin@example.com",
            "admin",
        )
        self.client.login(username="admin", password="admin")

    def get_actions(self):
        request = self.rf.get("/")
        request.user = self.admin_user
        return filter(
            lambda a: re.match(r"alter_field_\w+", a),
            self.admin.get_actions(request),
        )

    def assign_to_m2m(self):
        all_objects = list(self.RelatedTestModel.objects.all())
        chosen = sample(all_objects, randint(1, len(all_objects)))

        return [str(o.pk) for o in chosen], set(chosen)

    @override_settings(ROOT_URLCONF=__name__)
    def test_alter_field_action(self):
        all_objects = list(self.TestModel.objects.all())
        shuffle(all_objects)
        split = randint(1, len(all_objects) - 1)
        acted = all_objects[:split]
        not_acted = all_objects[split:]

        related = choice(self.RelatedTestModel.objects.all())
        new_values = {
            "name": lambda: ("zzz", "zzz"),
            "number": lambda: (42, 42),
            "rel": lambda: (related.pk, related),
            "m2m": self.assign_to_m2m,
        }

        for action_name in self.get_actions():
            data = {
                "action": action_name,
                ACTION_CHECKBOX_NAME: [f.pk for f in acted],
            }
            url = reverse(
                "admin_custom_urls:alter_field_action_testmodel_changelist"
            )
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)

            field_name = action_name.replace("alter_field_", "")
            (new_post_value, new_field_value) = new_values[field_name]()
            data[field_name] = new_post_value

            response = self.client.post(url, data, follow=True)
            self.assertEqual(response.status_code, 200)

            for obj in self.TestModel.objects.filter(
                pk__in=[o.pk for o in acted]
            ):
                obj_value = getattr(obj, field_name)
                if isinstance(
                    self.TestModel._meta.get_field(field_name),
                    models.ManyToManyField,
                ):
                    self.assertLessEqual(
                        new_field_value, set(obj_value.all())
                    )

                else:
                    self.assertEqual(new_field_value, obj_value)

            for oldo in not_acted:
                newo = self.TestModel.objects.get(pk=oldo.pk)
                self.assertEqual(
                    getattr(newo, field_name), getattr(oldo, field_name)
                )

    def test_invalid_one_to_one(self):
        with self.assertRaises(ValueError):
            alter_field_action(self.TestModel, "o2o")



urlpatterns = [
    path("admin/", AlterFieldActionTestCase.site.urls),
]
