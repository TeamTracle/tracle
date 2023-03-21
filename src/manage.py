#!/usr/bin/env python3
"""Django's command-line utility for administrative tasks."""
import os
import sys

from django.core.exceptions import ImproperlyConfigured

def main():
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        raise ImproperlyConfigured('DJANGO_SETTINGS_MODULE is not set.')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
