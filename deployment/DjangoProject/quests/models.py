from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class QuestTemplate(models.Model):
    class QuestType(models.TextChoices):
        WALK = "WALK", "Walk"
        CYCLE = "CYCLE", "Cycle"
        TRANSIT = "TRANSIT", "Public transport"
        MIXED = "MIXED", "Mixed / Any"

    #practical fields so we can actually display a quest card
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    #ER fields
    type = models.CharField(max_length=20, choices=QuestType.choices)
    group_limits = models.CharField(
        max_length=20,
        help_text="Format: min-max (e.g. 1-1, 1-4, 3-8)",
    )
    duration = models.PositiveSmallIntegerField(help_text="Duration in minutes")

    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    def fits_group_size(self, group_size: int) -> bool:
        """
        Returns True if group_size fits within group_limits (min-max).
        """
        try:
            min_s, max_s = self.group_limits.split("-", 1)
            min_g = int(min_s.strip())
            max_g = int(max_s.strip())
        except Exception:
            return False
        return min_g <= group_size <= max_g

class QuestRun(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"
        ABANDONED = "ABANDONED", "Abandoned"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quest_runs",
    )
    quest = models.ForeignKey(
        QuestTemplate,
        on_delete=models.PROTECT,
        related_name="runs",
    )
    city = models.ForeignKey(
        "world.City",
        on_delete=models.PROTECT,
        related_name="quest_runs",
    )

    # Keep the “stats” idea from the ER, but store common stats as columns (easy querying)
    group_size = models.PositiveSmallIntegerField()
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    time_minutes = models.PositiveIntegerField(null=True, blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    steps = models.PositiveIntegerField(null=True, blank=True)

    note = models.TextField(blank=True)
    proof_file = models.FileField(upload_to="proofs/", null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    def __str__(self) -> str:
        return f"Run {self.id} - {self.user.username} - {self.quest.name}"