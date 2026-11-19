"""
Every user-facing string must have a Romanian translation (see CLAUDE.md).

These tests read the templates and Python files, collect the English strings
marked for translation, and check each one is in locale/ro/LC_MESSAGES/django.po
with a non-empty Romanian text. They catch a forgotten translation before it
reaches the site, where it would show up in English.
"""

import pathlib
import re

from babel.messages.pofile import read_po
from django.conf import settings

ROOT = pathlib.Path(settings.BASE_DIR)
PO_FILE = ROOT / "locale" / "ro" / "LC_MESSAGES" / "django.po"


def catalogue():
    with PO_FILE.open("rb") as handle:
        return read_po(handle)


def singular(message_id):
    return message_id[0] if isinstance(message_id, tuple) else message_id


def strings_in_code():
    """English strings marked for translation in templates and Python code."""
    found = set()

    def add(text):
        text = re.sub(r"\s+", " ", text.strip())
        if text:
            found.add(text.split("{% plural %}")[0])

    for path in [*(ROOT / "templates").rglob("*.html"), *(ROOT / "templates").rglob("*.txt")]:
        text = path.read_text()
        for match in re.finditer(r"{%\s*translate\s+\"([^\"]+)\"", text):
            add(match.group(1))
        for match in re.finditer(r"{%\s*translate\s+'([^']+)'", text):
            add(match.group(1))
        for match in re.finditer(r"{%\s*blocktranslate[^%]*%}(.*?){%\s*endblocktranslate\s*%}", text, re.S):
            add(re.sub(r"{{\s*(\w+)\s*}}", r"%(\1)s", match.group(1)))
    for path in ROOT.glob("*/**/*.py"):
        if "tests" in path.parts or "migrations" in path.parts:
            continue
        text = path.read_text()
        for match in re.finditer(r"(?<![\w.])(?:_|gettext|ngettext)\(\s*\"([^\"]+)\"", text):
            add(match.group(1))
    return found


def test_every_string_has_a_romanian_translation():
    translated = {singular(message.id) for message in catalogue() if message.id}
    missing = sorted(strings_in_code() - translated)
    assert not missing, f"Add these to {PO_FILE.relative_to(ROOT)}: {missing}"


def test_no_translation_is_left_empty():
    empty = [
        singular(message.id)
        for message in catalogue()
        if message.id and (not message.string or (isinstance(message.string, tuple) and not all(message.string)))
    ]
    assert not empty, f"Translate these: {empty}"


def test_romanian_uses_comma_below_letters():
    """Romanian ș and ț take a comma below; ş and ţ (cedilla) are a common typing mistake."""
    assert not re.search("[şţŞŢ]", PO_FILE.read_text())
