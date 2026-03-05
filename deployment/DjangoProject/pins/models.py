from django.db import models
from django.conf import settings

# Create your models here.
class Pin(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    city = models.ForeignKey(
        "world.City",
        on_delete=models.CASCADE,
        related_name="pins",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pins",
    )

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    long = models.DecimalField(max_digits=9, decimal_places=6)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    #for seeded pins through Wikivoyage
    source_url = models.URLField(blank=True)
    is_seeded = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.city.name})"


class PinReport(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        REVIEWED = "REVIEWED", "Reviewed"
        DISMISSED = "DISMISSED", "Dismissed"

    pin = models.ForeignKey(Pin, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pin_reports")

    reason = models.CharField(max_length=120)
    details = models.TextField(blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["pin", "reporter", "reason"], name="unique_pin_report_per_reason")
        ]

    def __str__(self) -> str:
        return f"Report {self.id} on Pin {self.pin_id} ({self.status})"