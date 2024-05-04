from django.core.exceptions import ImproperlyConfigured
from django.forms.models import model_to_dict


# pylint: disable-next=too-few-public-methods
class DynamicAdminMixin:
    def each_context(self, *args, **kwargs):
        try:
            context = super().each_context(*args, **kwargs)
        except AttributeError as e:
            raise AttributeError(
                "Make sure to mix DynamicAdminMixin with admin.AdminSite"
            ) from e

        try:
            cls = self.site_configuration_model
        except AttributeError as e:
            raise ImproperlyConfigured(
                "Using DynamicAdminMixin requires setting the "
                + "'site_administration_model' attribute"
            ) from e

        try:
            conf = cls.objects.get()
        except cls.DoesNotExist:
            return context

        values = {
            k: v for k, v in model_to_dict(conf).items() if v and k != "id"
        }

        context.update(values)

        return context
