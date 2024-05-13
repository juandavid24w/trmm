from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import get_error_detail

import csvio

from .models import Email, Profile

User = get_user_model()


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ["email", "receive_notifications"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["grade"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    additional_emails = serializers.CharField(
        required=False,
        write_only=True,
        help_text=_(
            "Especifique emails separados por vírgula. Opcionalmente, "
            "coloque 0 ou 1, também separado por vírgula, depois de um "
            "email para indicar se esse email deve receber notificações "
            "ou não"
        ),
    )
    grade = serializers.ChoiceField(
        write_only=True,
        required=False,
        allow_blank=True,
        choices=Profile.Grade,
    )
    groups = serializers.CharField(write_only=True, required=False)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        emails = instance.additional_emails.all().values_list(
            "email", "receive_notifications"
        )
        ret["additional_emails"] = ",".join(
            str(int(v)) if isinstance(v, bool) else v.strip()
            for v in sum(emails, ())
        )

        try:
            ret["grade"] = instance.profile.grade
        except Profile.DoesNotExist:
            ret["grade"] = None

        ret["groups"] = ",".join(
            instance.groups.values_list("name", flat=True)
        )

        return ret

    @staticmethod
    def treat_emails(emails):
        words = emails.split(",")
        ret = []
        errors = []

        i = 0
        while i < len(words):
            try:
                validate_email(words[i])
            except ValidationError as exc:
                errors.append(exc.detail)
            except DjangoValidationError as exc:
                errors.append(get_error_detail(exc))
            else:
                if i + 1 < len(words) and words[i + 1] in ("0", "1"):
                    ret.append(
                        {
                            "email": words[i],
                            "receive_notifications": bool(int(words[i + 1])),
                        }
                    )
                    i += 2
                else:
                    ret.append({"email": words[i]})
                    i += 1

        return ret, errors

    def to_internal_value(self, data):
        data = super().to_internal_value(data).copy()
        errors = {}

        if "additional_emails" in data:
            data["additional_emails"], emails_errors = self.treat_emails(
                data["additional_emails"]
            )

            if emails_errors:
                errors["emails"] = emails_errors

        if "groups" in data:
            groups = data["groups"].split(",")

            if Group.objects.filter(
                name__in=groups
            ).distinct().count() != len(set(groups)):
                inexistent = []
                for name in groups:
                    if not Group.objects.filter(name=name).exists():
                        inexistent.append(name)

                errors["groups"] = [
                    _("Grupos inválidos: %(groups)s")
                    % {"groups": ", ".join(inexistent)}
                ]

            data["groups"] = groups

        if errors:
            raise ValidationError(errors)

        return data

    def create(self, validated_data):
        additional_emails = validated_data.pop("additional_emails", None)
        grade = validated_data.pop("grade", None)
        group_names = validated_data.pop("groups", None)

        user = User.objects.create_user(
            username=validated_data.pop("username"),
            password=validated_data.pop("password"),
        )

        for key, val in validated_data.items():
            setattr(user, key, val)

        user.save()

        if group_names:
            groups = Group.objects.filter(name__in=group_names)
            user.groups.add(*groups)

        if additional_emails:
            for email_data in additional_emails:
                user.additional_emails.create(**email_data)

        if grade:
            user.profile.create(grade=grade)

        return user

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "additional_emails",
            "grade",
            "groups",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
        ]

        read_only_fields = [
            "last_login",
            "date_joined",
        ]


csvio.register(User, UserSerializer)
