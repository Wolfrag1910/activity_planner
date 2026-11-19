"""
Fill the site with fake members and events for the private test.

    docker compose exec web python manage.py seed_test_data
    docker compose exec web python manage.py seed_test_data --reset   # start the fake data over

Every fake member has an @cumetria.test email address (".test" is a reserved
domain: mail to it goes nowhere). That is how this command recognises its own
data: --reset removes those members, the events they organized and every answer
on those events, and leaves everything else alone.

Dates are worked out from today (Bucharest time), so running it again later
gives fresh "today", "next week" and "last month" events.
"""

import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from events.models import RSVP, Category, Event, Guest
from members.models import Invite, Member

FAKE_EMAIL_DOMAIN = "@cumetria.test"
FAKE_INVITE_NAMES = ["Raluca (test)", "Victor (test)"]

GOING, MAYBE, NO = RSVP.Answer.GOING, RSVP.Answer.MAYBE, RSVP.Answer.NO
WORKING, AWAY = RSVP.Reason.WORKING, RSVP.Reason.AWAY
NOT_FEELING_IT, OTHER = RSVP.Reason.NOT_FEELING_IT, RSVP.Reason.OTHER


def fake_members():
    return Member.objects.filter(email__endswith=FAKE_EMAIL_DOMAIN)


def remove_fake_data():
    """Delete the fake members, their events (with all answers on them) and the test invites."""
    members = fake_members()
    Event.objects.filter(organizer__in=members).delete()
    members.delete()
    Invite.objects.filter(name__in=FAKE_INVITE_NAMES).delete()


class Command(BaseCommand):
    help = "Add fake members and events for testing (never on the live site after the reveal)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Remove the fake data made earlier, then create it again."
        )

    def handle(self, *args, reset, **options):
        owner = Member.objects.filter(is_admin=True).exclude(email__endswith=FAKE_EMAIL_DOMAIN).first()
        if owner is None:
            raise CommandError(
                "Create your own account first:\n"
                "  python manage.py create_owner --email you@gmail.com --name Alex"
            )
        if fake_members().exists() and not reset:
            raise CommandError("Fake data is already there. Run again with --reset to start it over.")

        with transaction.atomic():
            remove_fake_data()
            Seeder(owner).run()

        self.stdout.write(self.style.SUCCESS("Fake members and events are ready."))
        self.stdout.write(
            "To see the site as one of them: sign out, type e.g. ana@cumetria.test on the login\n"
            "page and open the sign-in link that appears in the `docker compose up` terminal.\n"
            "Ioana (ioana@cumetria.test) has answered nothing; Mihai is deactivated."
        )


class Seeder:
    """Builds the fake data. Each event below says in a comment what it is there to test."""

    def __init__(self, owner):
        self.owner = owner
        self.today = timezone.localdate()

    # --- Small helpers ---------------------------------------------------------------

    def day(self, offset):
        return self.today + datetime.timedelta(days=offset)

    def at(self, day, hour, minute=0):
        """A Bucharest date and time."""
        return timezone.make_aware(datetime.datetime.combine(day, datetime.time(hour, minute)))

    def event(self, organizer, category, title, starts_at, **fields):
        return Event.objects.create(
            organizer=self.people[organizer], category=category, title=title, starts_at=starts_at, **fields
        )

    def answer(self, event, who, answer, reason="", note="", guests=()):
        """`guests` is a list of names; an empty name ("") is a surprise guest."""
        rsvp = RSVP.objects.create(event=event, member=self.people[who], answer=answer, reason=reason, note=note)
        for name in guests:
            Guest.objects.create(rsvp=rsvp, name=name)

    def birthday(self, days_from_today, year):
        upcoming = self.day(days_from_today)
        # 1996 is a leap year, so 29 February is always a valid birthday there.
        return upcoming.replace(year=1996 if (upcoming.month, upcoming.day) == (2, 29) else year)

    # --- The data --------------------------------------------------------------------

    def run(self):
        self.create_members()
        self.create_invites()
        self.create_upcoming_events()
        self.create_past_events()
        # Mihai is deactivated last, so his past answers exist (they stay on the site).
        self.people["mihai"].is_active = False
        self.people["mihai"].save(update_fields=["is_active"])

    def create_members(self):
        def member(key, name, birthday=None, language=Member.Language.ROMANIAN, joined_days_ago=200):
            return Member.objects.create_user(
                email=f"{key}{FAKE_EMAIL_DOMAIN}",
                name=name,
                birthday=birthday,
                language=language,
                date_joined=timezone.now() - datetime.timedelta(days=joined_days_ago),
            )

        self.people = {
            "owner": self.owner,
            # Birthday in 5 days: the Members page highlights it as the next one.
            "ana": member("ana", "Ana Popescu", self.birthday(5, 1995)),
            # Prefers English.
            "bogdan": member("bogdan", "Bogdan Ionescu", datetime.date(1993, 3, 14), Member.Language.ENGLISH),
            "cristina": member("cristina", "Cristina Marin", datetime.date(1997, 7, 2)),
            "dan": member("dan", "Dan Stoica", datetime.date(1994, 11, 30)),
            "elena": member("elena", "Elena Dumitrescu", datetime.date(1996, 1, 21)),
            "florin": member("florin", "Florin Radu", datetime.date(1992, 9, 9)),
            # Joined two days ago, no birthday yet, has answered nothing.
            "ioana": member("ioana", "Ioana Vasile", joined_days_ago=2),
            # Deactivated (at the end of run()).
            "mihai": member("mihai", "Mihai Georgescu", datetime.date(1995, 5, 5)),
        }

    def create_invites(self):
        # The Admin page: one invite waiting to be used, one cancelled.
        Invite.objects.create(name=FAKE_INVITE_NAMES[0], created_by=self.owner)
        Invite.objects.create(name=FAKE_INVITE_NAMES[1], created_by=self.owner).cancel()

    def create_upcoming_events(self):
        # Today's plan: the evening picnic. Named guest, surprise guest, Maybe and No with reasons.
        picnic = self.event(
            "ana", Category.OUTDOORS, "Picnic în Herăstrău", self.at(self.today, 18, 30),
            place="Parcul Herăstrău, intrarea de la Arcul de Triumf", max_spots=12,
            description="Aducem pături și ceva de ronțăit. Eu iau limonadă.",
        )
        self.answer(picnic, "owner", GOING)
        self.answer(picnic, "ana", GOING)
        self.answer(picnic, "dan", GOING, guests=["Matei"])
        self.answer(picnic, "elena", GOING, guests=[""])
        self.answer(picnic, "florin", GOING)
        self.answer(picnic, "cristina", MAYBE, WORKING, "Ies de la birou pe la 19.")
        self.answer(picnic, "bogdan", NO, AWAY, "Sunt la Sibiu.")

        # A trip already under way: started yesterday, ends tomorrow.
        sibiu = self.event(
            "bogdan", Category.TRIPS, "Weekend la Sibiu", self.at(self.day(-1), 9),
            ends_at=self.at(self.day(1), 18), place="Sibiu, Piața Mare",
        )
        self.answer(sibiu, "bogdan", GOING, guests=["Irina"])
        self.answer(sibiu, "ana", NO, WORKING)

        # Waiting for the owner's answer; online, with a game and a link.
        minecraft = self.event(
            "dan", Category.GAMING, "Minecraft night", self.at(self.day(2), 21),
            game="Minecraft", online_link="https://discord.gg/cumetria-test",
            description="Construim baza nouă lângă râu.",
        )
        self.answer(minecraft, "dan", GOING)
        self.answer(minecraft, "florin", GOING)
        self.answer(minecraft, "bogdan", MAYBE, OTHER, "Depinde când ajung acasă.")
        self.answer(minecraft, "elena", NO, NOT_FEELING_IT)

        # Full: 4 spots, 3 members plus a surprise guest. The owner hasn't answered.
        climbing = self.event(
            "ana", Category.OUTDOORS, "Escaladă la sală", self.at(self.day(4), 19),
            place="Sala de escaladă, Militari", max_spots=4,
        )
        self.answer(climbing, "ana", GOING)
        self.answer(climbing, "cristina", GOING)
        self.answer(climbing, "elena", GOING, guests=[""])

        # The "answer by" time has passed, but the ride hasn't started: answers are closed.
        bike = self.event(
            "florin", Category.OUTDOORS, "Tură cu bicicleta în Văcărești", self.at(self.day(6), 10),
            answer_by=self.at(self.day(-1), 20), place="Parcul Natural Văcărești",
        )
        self.answer(bike, "florin", GOING)
        self.answer(bike, "dan", GOING)
        self.answer(bike, "cristina", NO, WORKING)

        # Friday to Monday, so the calendar bar crosses from one week into the next.
        # Every quick-pick reason appears here.
        friday = self.day((4 - self.today.weekday()) % 7 + 7)
        brasov = self.event(
            "bogdan", Category.TRIPS, "Brașov și Bran", self.at(friday, 8),
            ends_at=self.at(friday + datetime.timedelta(days=3), 20), max_spots=8,
            answer_by=self.at(self.day(5), 22), place="Gara de Nord, peronul 5",
            description="Mergem cu trenul de 8:00. Cazare la o pensiune în Șcheii Brașovului.",
        )
        self.answer(brasov, "bogdan", GOING)
        self.answer(brasov, "owner", GOING)
        self.answer(brasov, "dan", GOING, guests=["Matei"])
        self.answer(brasov, "cristina", MAYBE, WORKING)
        self.answer(brasov, "elena", MAYBE, AWAY, "Sunt la părinți până joi.")
        self.answer(brasov, "ana", NO, NOT_FEELING_IT)
        self.answer(brasov, "florin", NO, OTHER, "Am nunta unui văr.")

        # Gaming in person, no online link. The owner said Maybe.
        board_games = self.event(
            "dan", Category.GAMING, "Board games la Dan", self.at(self.day(10), 19),
            game="Catan", place="La Dan acasă, Drumul Taberei",
        )
        self.answer(board_games, "dan", GOING)
        self.answer(board_games, "elena", GOING)
        self.answer(board_games, "owner", MAYBE, OTHER, "Vin dacă termin proiectul.")
        self.answer(board_games, "ana", MAYBE, AWAY)

        # Cancelled after people had answered.
        kayak = self.event(
            "cristina", Category.OUTDOORS, "Caiac pe Snagov", self.at(self.day(12), 11),
            place="Lacul Snagov", status=Event.Status.CANCELLED,
        )
        self.answer(kayak, "cristina", GOING)
        self.answer(kayak, "ana", GOING)
        self.answer(kayak, "owner", GOING)

        # A day hike; the owner hasn't answered (second "waiting" item).
        hike = self.event(
            "ana", Category.OUTDOORS, "Drumeție în Piatra Craiului", self.at(self.day(20), 7),
            ends_at=self.at(self.day(20), 20), place="Zărnești, parcarea de la Prăpăstii",
            description="De adus: bocanci, apă, sandvișuri, geacă de ploaie.",
        )
        self.answer(hike, "ana", GOING)
        self.answer(hike, "florin", GOING)

        # Next month, starting near its end so the bar crosses into the month after.
        next_month = (self.today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        month_after = (next_month + datetime.timedelta(days=32)).replace(day=1)
        cluj_start = month_after - datetime.timedelta(days=2)
        cluj = self.event(
            "elena", Category.TRIPS, "Cluj și Cheile Turzii", self.at(cluj_start, 7),
            ends_at=self.at(cluj_start + datetime.timedelta(days=2), 21), place="Cluj-Napoca",
        )
        self.answer(cluj, "elena", GOING)
        self.answer(cluj, "owner", GOING)
        self.answer(cluj, "dan", MAYBE, AWAY)

        # A long holiday months away, with an "answer by" date. The owner hasn't answered.
        greece_start = self.day(210)
        greece = self.event(
            "bogdan", Category.VACATIONS, "Vară în Grecia", self.at(greece_start, 6),
            ends_at=self.at(greece_start + datetime.timedelta(days=7), 22), max_spots=10,
            answer_by=self.at(self.day(60), 22), place="Halkidiki, Grecia",
            description="Închiriem o casă pentru o săptămână. Avem nevoie de numărul de oameni ca să rezervăm.",
        )
        self.answer(greece, "bogdan", GOING)
        self.answer(greece, "ana", MAYBE, WORKING, "Trebuie să cer concediu.")

    def create_past_events(self):
        among_us = self.event(
            "dan", Category.GAMING, "Among Us online", self.at(self.day(-3), 21),
            game="Among Us", online_link="https://discord.gg/cumetria-test",
        )
        self.answer(among_us, "dan", GOING)
        self.answer(among_us, "florin", GOING)
        self.answer(among_us, "elena", GOING)
        self.answer(among_us, "owner", NO, WORKING)

        # Mihai (now deactivated) went: his answer stays visible.
        bbq = self.event(
            "florin", Category.OUTDOORS, "Grătar la Comana", self.at(self.day(-14), 12),
            ends_at=self.at(self.day(-14), 20), place="Parcul Natural Comana",
        )
        self.answer(bbq, "florin", GOING)
        self.answer(bbq, "owner", GOING)
        self.answer(bbq, "mihai", GOING)
        self.answer(bbq, "ana", GOING, guests=["Sora Anei"])
        self.answer(bbq, "cristina", NO, AWAY)

        rainy = self.event(
            "cristina", Category.OUTDOORS, "Muzeul Satului", self.at(self.day(-21), 11),
            place="Muzeul Național al Satului", status=Event.Status.CANCELLED,
            description="Anulat: plouă toată ziua.",
        )
        self.answer(rainy, "cristina", GOING)
        self.answer(rainy, "mihai", MAYBE, NOT_FEELING_IT)

        sinaia = self.event(
            "ana", Category.TRIPS, "Sinaia", self.at(self.day(-35), 8),
            ends_at=self.at(self.day(-34), 19), place="Sinaia, Castelul Peleș",
        )
        self.answer(sinaia, "ana", GOING)
        self.answer(sinaia, "owner", GOING)
        self.answer(sinaia, "mihai", GOING)
        self.answer(sinaia, "bogdan", GOING)
        self.answer(sinaia, "elena", MAYBE, WORKING)

        vama = self.event(
            "elena", Category.VACATIONS, "Vama Veche", self.at(self.day(-120), 9),
            ends_at=self.at(self.day(-115), 18), place="Vama Veche",
        )
        for who in ["elena", "ana", "dan", "owner", "mihai"]:
            self.answer(vama, who, GOING)
