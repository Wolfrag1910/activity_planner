import secrets

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class MemberManager(BaseUserManager):
    """Creates members. Nobody has a password: they sign in with Google or an emailed link."""

    def create_user(self, email, name, **extra_fields):
        if not email:
            raise ValueError("A member needs an email address.")
        member = self.model(email=self.normalize_email(email).lower(), name=name, **extra_fields)
        member.set_unusable_password()
        member.save(using=self._db)
        return member

    def create_superuser(self, email, name, password=None, **extra_fields):
        # Used by Django's `createsuperuser` command; the owner normally uses `create_owner`.
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, name, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class Member(AbstractBaseUser, PermissionsMixin):
    """One person in the group. See "What the site stores" in docs/PLAN.md."""

    class Language(models.TextChoices):
        ROMANIAN = "ro", "Română"
        ENGLISH = "en", "English"

    class Look(models.TextChoices):
        PICNIC = "picnic", "Sunday Picnic"
        POSTCARD = "postcard", "Postcard"

    class Mode(models.TextChoices):
        LIGHT = "light", _("Light")
        DARK = "dark", _("Dark")
        AUTO = "auto", _("Match my phone")

    email = models.EmailField(_("email"), unique=True)
    name = models.CharField(_("name"), max_length=60)
    photo = models.ImageField(_("photo"), upload_to="members/", blank=True)
    birthday = models.DateField(_("birthday"), null=True, blank=True)
    language = models.CharField(
        _("language"), max_length=2, choices=Language.choices, default=Language.ROMANIAN
    )
    look = models.CharField(_("look"), max_length=10, choices=Look.choices, default=Look.PICNIC)
    mode = models.CharField(_("light or dark"), max_length=5, choices=Mode.choices, default=Mode.LIGHT)

    # The owner. Can invite and deactivate members, edit or cancel any event, delete photos.
    is_admin = models.BooleanField(_("admin"), default=False)
    # A deactivated member can't sign in, but everything they did stays on the site.
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("joined"), default=timezone.now)

    objects = MemberManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["name"]
        verbose_name = _("member")
        verbose_name_plural = _("members")

    def __str__(self):
        return self.name

    @property
    def is_staff(self):
        """Django's built-in admin (/django-admin/) is for the owner only."""
        return self.is_admin

    @property
    def initial(self):
        return self.name[:1].upper()

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)


def new_invite_token():
    return secrets.token_urlsafe(24)


class Invite(models.Model):
    """A personal, single-use link the admin creates and sends to a new member."""

    token = models.CharField(max_length=64, unique=True, default=new_invite_token, editable=False)
    name = models.CharField(_("name"), max_length=60)
    created_by = models.ForeignKey(
        Member, null=True, on_delete=models.SET_NULL, related_name="invites_sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.OneToOneField(
        Member, null=True, blank=True, on_delete=models.SET_NULL, related_name="invite"
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("invite")
        verbose_name_plural = _("invites")

    def __str__(self):
        return self.name

    @property
    def is_usable(self):
        return self.used_at is None and self.cancelled_at is None

    def mark_used(self, member):
        self.used_at = timezone.now()
        self.used_by = member
        self.save(update_fields=["used_at", "used_by"])

    def cancel(self):
        self.cancelled_at = timezone.now()
        self.save(update_fields=["cancelled_at"])

    @classmethod
    def usable(cls, token):
        """The invite for this token if it can still be used, otherwise None."""
        if not token:
            return None
        return cls.objects.filter(token=token, used_at=None, cancelled_at=None).first()
