from django.db import models
from django.conf import settings

# Create your models here.

class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        HIDDEN = "HIDDEN", "Hidden"
        DELETED = "DELETED", "Deleted"

    # One run → max one post (run_id is unique)
    run = models.OneToOneField(
        "quests.QuestRun",
        on_delete=models.CASCADE,
        related_name="post",
    )

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Post {self.id} (run {self.run_id})"

class Comment(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        HIDDEN = "HIDDEN", "Hidden"
        DELETED = "DELETED", "Deleted"

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    text = models.TextField()

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Comment {self.id} by {self.user.username} on Post {self.post_id}"

class Reaction(models.Model):
    class ReactionType(models.TextChoices):
        LIKE = "LIKE", "Like"
        LOVE = "LOVE", "Love"
        LAUGH = "LAUGH", "Laugh"
        WOW = "WOW", "Wow"
        SAD = "SAD", "Sad"
        ANGRY = "ANGRY", "Angry"

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions",
    )

    reaction_type = models.CharField(
        max_length=10,
        choices=ReactionType.choices,
        default=ReactionType.LIKE,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_reaction_per_user_per_post")
        ]

    def __str__(self) -> str:
        return f"{self.reaction_type} by {self.user.username} on Post {self.post_id}"