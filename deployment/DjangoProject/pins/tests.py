from django.test import TestCase, Client
from accounts.models import User
from world.models import City
from pins.models import Pin

# Create your test here.
class PinListTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.city = City.objects.create(name="Glasgow", lat=55.8642, long=-4.2518)

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
        )
        self.user.selected_city = self.city
        self.user.save()

        #approved pin should appear
        Pin.objects.create(
            city=self.city,
            user=self.user,
            title="Approved Place",
            description="Visible",
            lat=55.8600,
            long=-4.2500,
            status=Pin.Status.APPROVED,
        )

        #pending pin should NOT! appear
        Pin.objects.create(
            city=self.city,
            user=self.user,
            title="Pending Place",
            description="Not visible yet",
            lat=55.8610,
            long=-4.2510,
            status=Pin.Status.PENDING,
        )

    def test_pin_list_returns_only_approved_pins(self):
        ok = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(ok)

        resp = self.client.get("/pins/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        titles = [p["title"] for p in data["results"]]

        self.assertIn("Approved Place", titles)
        self.assertNotIn("Pending Place", titles)