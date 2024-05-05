"""
WSGI config for biblioteca project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

base_dir = Path(__file__).parent.parent


def get_env_file():
    file = Path(base_dir / ".env")
    if file.is_file():
        with open(file, "r", encoding="utf-8") as f:
            for line in f.readlines():
                if line.strip() and "=" in line:
                    a, b = map(str.strip, line.split("=", 1))
                    os.environ.setdefault(a, b.strip('"'))

get_env_file()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "biblioteca.settings")

application = get_wsgi_application()
