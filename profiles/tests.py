# from django.test import TestCase
from unittest import TestCase

from .models import Profile


class TestGradeEnum(TestCase):
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
