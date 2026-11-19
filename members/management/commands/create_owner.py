from django.core.management.base import BaseCommand

from members.models import Member


class Command(BaseCommand):
    help = "Create the owner's account (the admin), or make an existing member the admin."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="The owner's email (the Google account they'll use).")
        parser.add_argument("--name", required=True, help="The name shown on the site.")

    def handle(self, *args, email, name, **options):
        member = Member.objects.filter(email__iexact=email).first()
        if member is None:
            member = Member.objects.create_user(email=email, name=name, is_admin=True, is_superuser=True)
            self.stdout.write(self.style.SUCCESS(f"Created the owner account for {member.email}."))
        else:
            member.is_admin = True
            member.is_superuser = True
            member.is_active = True
            member.save()
            self.stdout.write(self.style.SUCCESS(f"{member.email} is now the admin."))
