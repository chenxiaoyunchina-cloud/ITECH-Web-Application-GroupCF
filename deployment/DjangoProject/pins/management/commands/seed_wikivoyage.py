from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from world.models import City
from pins.models import Pin
from pins.services.wikivoyage import fetch_city_wikitext, extract_places_from_wikitext


class Command(BaseCommand):
    help = "Seed APPROVED pins for a city from Wikivoyage listing templates."

    def add_arguments(self, parser):
        parser.add_argument("--city-id", type=int, required=True, help="City ID from your database (world_city).")
        parser.add_argument(
            "--page-title",
            type=str,
            default=None,
            help="Optional Wikivoyage page title override.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Max number of pins to import. 50 pins by default",
        )
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Delete previously seeded pins for this city before importing.",
        )

    def handle(self, *args, **options):
        city_id = options["city_id"]
        limit = options["limit"]
        refresh = options["refresh"]
        page_title = options["page_title"]

        if limit <= 0:
            raise CommandError("--limit must be > 0")

        city = City.objects.filter(pk=city_id).first()
        if not city:
            raise CommandError(f"City with id={city_id} not found")

        title = page_title or city.name

        self.stdout.write(self.style.NOTICE(f"Fetching Wikivoyage wikitext for: {title}"))
        try:
            wikitext = fetch_city_wikitext(title)
        except Exception as e:
            raise CommandError(f"Failed to fetch Wikivoyage content: {e}")

        places = extract_places_from_wikitext(title, wikitext, limit=limit)
        if not places:
            raise CommandError(
                "No mappable listings found (lat/long missing). Try a different --page-title or increase limit."
            )

        with transaction.atomic():
            if refresh:
                deleted, _ = Pin.objects.filter(city=city, is_seeded=True).delete()
                self.stdout.write(self.style.WARNING(f"Refresh enabled: deleted {deleted} seeded pin(s)."))

            created = 0
            skipped = 0

            for place in places:
                #if a seeded pin with same title and coords exists, skip it
                exists = Pin.objects.filter(
                    city=city,
                    is_seeded=True,
                    title=place.title,
                    lat=place.lat,
                    long=place.long,
                ).exists()

                if exists:
                    skipped += 1
                    continue

                Pin.objects.create(
                    city=city,
                    user_id=1,  #will be overwritten below if we can find a moderator/admin
                    title=place.title,
                    description=place.description,
                    lat=place.lat,
                    long=place.long,
                    status=Pin.Status.APPROVED,
                    source_url=place.source_url,
                    is_seeded=True,
                )
                created += 1

            from accounts.models import User  #intentional local import to avoid circulars at startup

            seed_owner = (
                User.objects.filter(is_staff=True).order_by("id").first()
                or User.objects.filter(role__in=["ADMIN", "MODERATOR"]).order_by("id").first()
                or User.objects.order_by("id").first()
            )
            if seed_owner:
                Pin.objects.filter(city=city, is_seeded=True, user_id=1).update(user=seed_owner)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created} seeded pin(s), skipped {skipped} duplicate(s), city={city.name}."
        ))