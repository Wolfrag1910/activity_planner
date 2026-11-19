from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from members.models import Invite, Member


class Command(BaseCommand):
    help = "Create an invite link for a new member (the Admin page will do this from step 2b)."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True, help="The new member's name, as it will appear on the site.")
        parser.add_argument(
            "--site", default="http://localhost:8080", help="The site's address, used to print the full link."
        )

    def handle(self, *args, name, site, **options):
        owner = Member.objects.filter(is_admin=True).order_by("date_joined").first()
        invite = Invite.objects.create(name=name, created_by=owner)
        self.stdout.write(f"{site.rstrip('/')}{reverse('invite', args=[invite.token])}")
