# Dynamic admin configuration

Define admin site configuration values dynamically. Simple wrapper
around [`django-solo`](https://github.com/lazybird/django-solo) to
configure admin site in the admin panel itself. Allows the configuration
of the following `AdminSite` attributes:

* `site_header`
* `site_title`
* `site_url`
* `index_title`
* `empty_value_display`
* `enable_nav_sidebar`

For more details on these attributes, refer to the
[documentation](https://docs.djangoproject.com/en/dev/ref/contrib/admin/#adminsite-attributes).


## How to use

1. Add `dynamic_admin_site` and `solo` to your `INSTALLED_APPS` in your
   project's `settings.py`
2. `python manage.py migrate`
3. Create a singleton model subclassing
   `dynamic_admin_site.models.SiteConfigurationModel`, containing any
   other field's you'd like:

```python
from django.db import models
from dynamic_admin_site.models import SiteConfigurationModel

class SiteConfiguration(SiteConfigurationModel):
    welcome_msg = models.TextField(blank=True)
    ...
```

   If you'd like your model to control only a subset of the available
   fields, use the provided factory to create the base model:

```python
from django.db import models
from dynamic_admin_site.models import site_configuration_factory

SiteConfigurationModel = site_configuration_factory(
    "site_title", "site_header", "index_title"
)

class SiteConfiguration(SiteConfigurationModel):
    welcome_msg = models.TextField(blank=True)
    ...
```


   If you need fine-grain control over the fields, subclass
   `solo.models.SingletonModel` instead and define them yourself:

```python
from django.db import models
from solo.models import SingletonModel

class SiteConfiguration(SingletonModel):
    site_header = models.TextField(blank=False, verbose_name="other name")
    ...

```

4. Subclass your admin site with
   `dynamic_admin_site.site.DynamicAdminMixin` and set the
   `site_configuration_model` attribute with the model created above,
   e.g.:

```python
# myproject/admin.py

from django.contrib import admin

from dynamic_admin_site.site import DynamicAdminMixin
from site_configuration.models import SiteConfiguration

class MyAdminSite(DynamicAdminMixin, admin.AdminSite):
    site_configuration_model = SiteConfiguration

    site_title = "Default title"
    site_header = "Default header"
    index_title = "Default index"
```

For more information about custom admin sites, refer to the
[documentation](https://docs.djangoproject.com/en/dev/ref/contrib/admin/#adminsite-objects).

## Default fields

### `site_header`

```python
models.CharField(
    max_length=255, blank=True, null=True, verbose_name=_("Cabeçalho do site")
)
```

### `site_title`

```python
models.CharField(
    max_length=255, blank=True, null=True, verbose_name=_("Título do site")
)
```

### `site_url`

```python
models.CharField(
    max_length=255,
    blank=True,
    null=True,
    verbose_name=_("Link para o site principal"),
)
```

### `index_title`

```python
models.CharField(
    max_length=255,
    blank=True,
    null=True,
    verbose_name=_("Título da página principal"),
)
```

### `empty_value_display`

```python
models.CharField(
    max_length=255,
    blank=True,
    null=True,
    verbose_name=_("Exibição de valores vazios"),
)
```

### `enable_nav_sidebar`

```python
models.BooleanField(
    verbose_name=_("Habilitar barra lateral de navegação"),
)
```


## Dependencies

* [`django-solo`](https://github.com/lazybird/django-solo)
