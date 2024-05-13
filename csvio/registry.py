from dataclasses import dataclass
from typing import Any

from django.apps import apps
from django.db.models import Model
from django.db.models.fields import NOT_PROVIDED
from rest_framework.serializers import Serializer


def has_default(field):
    return hasattr(field, "default") and field.default != NOT_PROVIDED


@dataclass
class Register:
    model: Model
    serializer: Serializer
    name: str
    label: Any
    use_with: str


class CSVIORegistry:
    _registry = {}

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)

    @classmethod
    def register(
        cls, model, serializer, name=None, label=None, use_with="both"
    ):
        assert use_with in ("both", "export", "import")

        key = f"{model._meta.app_label}.{model._meta.model_name}.{name or 'default'}"
        cls._registry[key] = Register(
            model=model,
            serializer=serializer,
            label=label or model._meta.verbose_name,
            name=name or "default",
            use_with=use_with,
        )

    @classmethod
    def items(cls, export=None):
        if export is None:
            return cls._registry.items()

        return [
            (k, r)
            for k, r in cls._registry.items()
            if (export and r.use_with != "import")
            or (not export and r.use_with != "export")
        ]

    @classmethod
    def get_model_choices(cls, export):
        choices = {}
        for key, reg in cls.items(export):
            app_label = reg.model._meta.app_label
            if app_label not in choices:
                choices[app_label] = (
                    apps.get_app_config(app_label).verbose_name,
                    [],
                )

            choices[app_label][1].append((key, reg.label))

        choices = list(choices.values())
        for _, models in choices:
            models.sort(key=lambda x: x[1])

        choices.sort(key=lambda x: x[0])
        return choices

    @classmethod
    def get_model_import_choices(cls):
        return cls.get_model_choices(export=False)

    @classmethod
    def get_model_export_choices(cls):
        return cls.get_model_choices(export=True)

    @classmethod
    def get_model_fields(cls, export):
        data = {}
        for key, reg in cls.items(export):
            serializer = reg.serializer()
            writable = [
                name
                for name, field in serializer.get_fields().items()
                if not field.read_only
            ]
            editable = [
                f
                for f in reg.model._meta.fields
                if hasattr(f, "editable") and f.editable
            ]
            mandatory = [
                f.name
                for f in editable
                if f.name in writable
                and not (hasattr(f, "blank") and f.blank)
                and not has_default(f)
            ]
            optional = [name for name in writable if name not in mandatory]
            data[key] = {"optional": optional, "mandatory": mandatory}

        return data
