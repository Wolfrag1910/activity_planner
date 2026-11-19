from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Invite, Member
from .photos import prepare_profile_photo


class ProfileForm(forms.ModelForm):
    """What a member can change about themselves."""

    photo_upload = forms.ImageField(label=_("New photo"), required=False)
    remove_photo = forms.BooleanField(label=_("Remove my photo"), required=False)

    class Meta:
        model = Member
        fields = ["name", "birthday", "language"]
        labels = {"name": _("Name"), "birthday": _("Birthday"), "language": _("Language")}
        widgets = {
            "birthday": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "language": forms.RadioSelect,
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError(_("Please enter a name."))
        return name

    def clean_photo_upload(self):
        upload = self.cleaned_data.get("photo_upload")
        return prepare_profile_photo(upload) if upload else None

    def save(self, commit=True):
        member = super().save(commit=False)
        new_photo = self.cleaned_data.get("photo_upload")
        if new_photo or self.cleaned_data.get("remove_photo"):
            if member.photo:
                member.photo.delete(save=False)  # don't leave the old file behind
            if new_photo:
                member.photo.save(new_photo.name, new_photo, save=False)
        if commit:
            member.save()
        return member


class InviteForm(forms.ModelForm):
    class Meta:
        model = Invite
        fields = ["name"]
        labels = {"name": _("Their name")}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError(_("Please enter a name."))
        return name
