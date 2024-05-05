from dataclasses import asdict, dataclass
from typing import Any, Callable

from django import forms
from django.core.exceptions import ImproperlyConfigured


@dataclass
class AdminButtonOptions:
    name: str
    method: str | None | Callable = None
    condition: Callable | bool | None = True
    extra_html: Any = None
    label: Any = None
    use_separator: bool = True

    def asdict(self):
        return asdict(self)


class AdminButtonsMixin:
    change_form_template = "admin_buttons/change_form.html"

    def __init__(self, *args, **kwargs):
        self._configure_admin_buttons()
        super().__init__(*args, **kwargs)

    def _configure_admin_buttons(self):
        try:
            self._admin_buttons_config = self.admin_buttons_config
        except AttributeError:
            self._admin_buttons_config = []

        for i, o in enumerate(self._admin_buttons_config):
            try:
                if not isinstance(o, AdminButtonOptions):
                    self._admin_buttons_config[i] = AdminButtonOptions(**o)
            except TypeError as e:
                raise ImproperlyConfigured(
                    "admin_buttons_config is not AdminButtonsOptions or "
                    + f"is not dictionary with the right keys: '{o}'"
                ) from e

    def response_change(self, request, obj, *args, **kwargs):
        for options in self._admin_buttons_config:
            if isinstance(options.method, str):
                method = getattr(self, options.method)

            if options.name in request.POST:
                return method(request, obj)

        return super().response_change(request, obj, *args, **kwargs)

    def _admin_buttons_get_extra_context(self, request, context):
        config = []

        for o in self._admin_buttons_config:
            options = {}
            for key, val in o.asdict().items():
                if val is not None:
                    try:
                        options[key] = val(request, context)
                    except TypeError:
                        options[key] = val

            config.append(options)

        extra_context = context or {}
        extra_context["admin_buttons_config"] = config
        return extra_context

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = self._admin_buttons_get_extra_context(
            request, extra_context
        )

        return super().add_view(request, form_url, extra_context)

    def change_view(
        self, request, object_id, form_url="", extra_context=None
    ):
        extra_context = self._admin_buttons_get_extra_context(
            request, extra_context
        )

        return super().change_view(
            request, object_id, form_url, extra_context
        )

    @property
    def media(self):
        return super().media + forms.Media(
            css={"all": ["admin_buttons/custom_submit_row.css"]}
        )
