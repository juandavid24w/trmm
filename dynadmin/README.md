# Dynamic admin configuration

Define admin site configuration values dynamically. Simple wrapper
around [`django-solo`](https://github.com/lazybird/django-solo) to
configure admin site in the admin panel itself.

## How to use

* Add `dynadmin` and `solo` to your `INSTALLED_APPS` in you project's `settings.py`
* `python manage.py migrate`
* Subclass your admin site with `dynadmin.site.DynamicAdminMixin`, e.g.:

```python
from django.contrib import admin

from dynadmin.site import DynamicAdminMixin


class MyAdminSite(DynamicAdminMixin, admin.AdminSite):
    site_title = "Default title"
    site_header = "Default header"
    index_title = "Default index"
```

## Dependencies

* [`django-solo`](https://github.com/lazybird/django-solo)
