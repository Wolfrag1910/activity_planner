class AccessibleErrorsMixin:
    """
    After checking a form, mark each field with an error as invalid and point it
    at its error message, so screen readers announce what to fix.
    The message itself is shown by templates/partials/field.html.
    """

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs["aria-invalid"] = "true"
                widget.attrs["aria-describedby"] = f"{self[name].auto_id}-error"
