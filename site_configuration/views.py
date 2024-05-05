from django.contrib import messages
from django.contrib.auth.views import (
    PasswordResetView as BasePasswordResetView,
)
from django.utils.translation import gettext_lazy as _

from site_configuration.models import EmailConfiguration


class PasswordResetView(BasePasswordResetView):
    """Only allow password resetting if email is activated"""

    def post(self, request, *args, **kwargs):
        conf = EmailConfiguration.get_solo()
        if not conf.activated:
            messages.error(
                request,
                _(
                    "Não foi possível redefinir a senha no momento. Por "
                    + "favor, contate os administradores do site."
                ),
            )
            form = self.get_form()
            return self.form_invalid(form)

        return super().post(request, *args, **kwargs)
