from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _


class DefaultObjectMixin(models.Model):
    is_default = models.BooleanField(
        verbose_name=_("É o padrão?"),
        default=False,
    )

    @classmethod
    def get_default(cls):
        try:
            return cls.objects.get(is_default=True)
        except cls.DoesNotExist:
            obj = cls.objects.first()
            if not obj:
                try:
                    return cls.objects.create(is_default=True)
                except IntegrityError:
                    pass
            return obj

    def save(self, *args, **kwargs):
        if self.is_default:
            try:
                old = self.__class__.objects.get(is_default=True)
                if old != self:
                    old.is_default = False
                    old.save()
            except self.__class__.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="%(app_label)s_%(class)s_unique_default",
            )
        ]
