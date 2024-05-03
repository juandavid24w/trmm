from django.forms.models import model_to_dict

from .models import SiteConfiguration


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
            conf = SiteConfiguration.objects.get()
        except SiteConfiguration.DoesNotExist:
            return context
        values = {
            k: v for k, v in model_to_dict(conf).items() if v and k != "id"
        }
        context.update(values)

        return context
