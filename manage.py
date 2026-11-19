#!/usr/bin/env python
"""Django's command-line tool: run `python manage.py help` to see the commands."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cumetria.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
