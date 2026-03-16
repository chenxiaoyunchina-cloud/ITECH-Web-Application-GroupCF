from django.core.management.base import BaseCommand
from world.models import City


class Command(BaseCommand):
    help = "Seed initial cities with coordinates"

    def handle(self, *args, **kwargs):

        cities = [
            ("Aberdeen", 57.1497, -2.0943),
            ("Belfast", 54.5973, -5.9301),
            ("Birmingham", 52.4862, -1.8904),
            ("Bristol", 51.4545, -2.5879),
            ("Cardiff", 51.4816, -3.1791),
            ("Edinburgh", 55.9533, -3.1883),
            ("Glasgow", 55.8642, -4.2518),
            ("Leeds", 53.8008, -1.5491),
            ("Leicester", 52.6369, -1.1398),
            ("Liverpool", 53.4084, -2.9916),
            ("London", 51.5074, -0.1278),
            ("Manchester", 53.4808, -2.2426),
            ("Newcastle upon Tyne", 54.9783, -1.6178),
            ("Nottingham", 52.9548, -1.1581),
            ("Sheffield", 53.3811, -1.4701),
        ]

        for name, lat, long in cities:

            city, created = City.objects.get_or_create(
                name=name,
                defaults={
                    "lat": lat,
                    "long": long
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created city: {name}"))
            else:
                self.stdout.write(f"City already exists: {name}")