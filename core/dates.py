"""Dates written the way people write them, in Romanian or English."""

import datetime

from django.utils import formats, translation


def _natural_case(text):
    """Romanian writes month and weekday names in lowercase; only the first letter is capitalised."""
    if translation.get_language() == "ro":
        return text.lower().capitalize()
    return text


def friendly_date(day):
    """'Thursday, 19 November' / 'Joi, 19 noiembrie'."""
    return _natural_case(formats.date_format(day, "l, j F"))


def day_and_month(day):
    """'3 March' / '3 martie'."""
    text = formats.date_format(day, "j F")
    return text.lower() if translation.get_language() == "ro" else text


def next_birthday(birthday, today):
    """The date of the next birthday on or after today (29 February counts as 28 February in other years)."""
    for year in (today.year, today.year + 1):
        try:
            candidate = birthday.replace(year=year)
        except ValueError:  # 29 February in a non-leap year
            candidate = datetime.date(year, 2, 28)
        if candidate >= today:
            return candidate
    raise AssertionError("unreachable")


def age_on(birthday, day):
    """How old someone born on `birthday` is on `day`."""
    before_birthday = (day.month, day.day) < (birthday.month, birthday.day)
    return day.year - birthday.year - (1 if before_birthday else 0)
