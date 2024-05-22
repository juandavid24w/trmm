import unittest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from biblioteca.admin import BibliotecaAdminSite

from .admin import UserAdmin
from .models import Profile

User = get_user_model()


class TestGradeEnum(unittest.TestCase):
    def test_succ_grade(self):
        for grade, nxt in (
            ("6EF", "7EF"),
            ("7EF", "8EF"),
            ("8EF", "9EF"),
            ("9EF", "1EM"),
            ("1EM", "2EM"),
            ("2EM", "3EM"),
        ):
            self.assertEqual(
                Profile.Grade(grade).next(), Profile.Grade(nxt), msg=grade
            )

        self.assertEqual(Profile.Grade("3EM").next(), Profile.Grade.__empty__)

    def test_prev_grade(self):
        for grade, nxt in (
            ("7EF", "6EF"),
            ("8EF", "7EF"),
            ("9EF", "8EF"),
            ("1EM", "9EF"),
            ("2EM", "1EM"),
            ("3EM", "2EM"),
        ):
            self.assertEqual(
                Profile.Grade(grade).prev(), Profile.Grade(nxt), msg=grade
            )

        self.assertEqual(Profile.Grade("6EF").prev(), Profile.Grade.__empty__)


def create_test_groups():
    usergroup, _ = Group.objects.get_or_create(name="Usuário")
    usergroup.permissions.add(Permission.objects.get(codename="view_book"))
    usergroup.permissions.add(
        Permission.objects.get(codename="view_specimen")
    )
    usergroup.permissions.add(
        Permission.objects.get(codename="view_classification")
    )
    usergroup.permissions.add(
        Permission.objects.get(codename="view_location")
    )
    usergroup.permissions.add(Permission.objects.get(codename="view_loan"))
    usergroup.permissions.add(Permission.objects.get(codename="view_period"))
    usergroup.permissions.add(Permission.objects.get(codename="view_renewal"))

    modgroup, _ = Group.objects.get_or_create(name="Moderador")
    modgroup.permissions.add(Permission.objects.get(codename="view_book"))
    modgroup.permissions.add(Permission.objects.get(codename="add_book"))
    modgroup.permissions.add(Permission.objects.get(codename="change_book"))
    modgroup.permissions.add(Permission.objects.get(codename="delete_book"))
    modgroup.permissions.add(Permission.objects.get(codename="view_specimen"))
    modgroup.permissions.add(Permission.objects.get(codename="add_specimen"))
    modgroup.permissions.add(
        Permission.objects.get(codename="change_specimen")
    )
    modgroup.permissions.add(
        Permission.objects.get(codename="delete_specimen")
    )
    modgroup.permissions.add(
        Permission.objects.get(codename="view_classification")
    )
    modgroup.permissions.add(Permission.objects.get(codename="view_location"))
    modgroup.permissions.add(Permission.objects.get(codename="view_loan"))
    modgroup.permissions.add(Permission.objects.get(codename="add_loan"))
    modgroup.permissions.add(Permission.objects.get(codename="change_loan"))
    modgroup.permissions.add(Permission.objects.get(codename="delete_loan"))
    modgroup.permissions.add(Permission.objects.get(codename="view_period"))
    modgroup.permissions.add(Permission.objects.get(codename="view_renewal"))
    modgroup.permissions.add(
        Permission.objects.get(codename="view_documentationpage")
    )
    modgroup.permissions.add(
        Permission.objects.get(codename="change_documentationpage")
    )
    modgroup.permissions.add(
        Permission.objects.get(codename="add_documentationpage")
    )
    modgroup.permissions.add(
        Permission.objects.get(codename="delete_documentationpage")
    )

    return usergroup, modgroup


def create_test_users():
    usergroup, modgroup = create_test_groups()
    user1 = User.objects.create_user(
        username="user1",
        password="1234",
        first_name="John",
        last_name="Dickson",
        email="myemail@server.com",
    )
    user1.profile = Profile()
    user1.groups.add(usergroup)
    user1.profile.grade = Profile.Grade.EF6
    user1.profile.save()
    user1.additional_emails.create(
        email="example@example.com",
        receive_notifications=True,
    )
    user1.additional_emails.create(
        email="uau@example.com",
        receive_notifications=False,
    )
    user1.additional_emails.create(email="hmmm@example.com")

    user2 = User.objects.create_user(
        username="user2",
        password="1234",
        first_name="João",
        last_name="do seu Rique",
        email="youremail@server.com",
    )
    user2.profile = Profile()
    user2.profile.grade = Profile.Grade.EM2
    user2.profile.save()
    user2.groups.add(usergroup)
    user2.additional_emails.create(
        email="not@example.com",
        receive_notifications=True,
    )
    user2.additional_emails.create(
        email="yes@example.com",
        receive_notifications=True,
    )

    user3 = User.objects.create(
        username="user3",
        password="abcde",
        first_name="Godofredo",
        last_name="Silvason",
        email="test@server.com",
    )
    user3.profile = Profile()
    user3.groups.add(usergroup)
    user3.groups.add(modgroup)
    user3.profile.save()

    user4 = User.objects.create_user(
        username="user4",
        password="1234",
        first_name="Pedro",
        last_name="Costa",
        email="test2@example.com",
    )
    user4.profile = Profile()
    user4.profile.grade = Profile.Grade.EM3
    user4.profile.save()
    user4.additional_emails.create(
        email="not@hmmm.com",
        receive_notifications=True,
    )
    user4.additional_emails.create(
        email="yes@hmmmm.com",
        receive_notifications=True,
    )


class ProfileTestCase(TestCase):
    def test_profile_creation(self):
        profile = Profile()
        user = User.objects.create_user(
            username="user_a",
            password="1234",
            first_name="John",
            last_name="Dickson",
            profile=profile,
        )
        profile.save()

        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.grade, Profile.Grade.__empty__)
        user.profile.grade = Profile.Grade.EF6
        user.profile.save()

        user = User.objects.get(username="user_a")
        self.assertEqual(user.profile.grade, Profile.Grade.EF6)

    def test_creation(self):
        create_test_users()
