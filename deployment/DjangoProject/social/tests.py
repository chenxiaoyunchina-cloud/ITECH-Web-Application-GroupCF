from django.test import TestCase, Client

from accounts.models import User
from world.models import City
from quests.models import QuestTemplate, QuestRun
from social.models import Post, Reaction


class ReactionOptionATests(TestCase):
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

        quest = QuestTemplate.objects.create(
            name="Test Quest",
            description="",
            type=QuestTemplate.QuestType.WALK,
            group_limits="1-5",
            duration=30,
            is_active=True,
        )

        run = QuestRun.objects.create(
            user=self.user,
            quest=quest,
            city=self.city,
            group_size=2,
            status=QuestRun.Status.COMPLETED,
        )

        self.post = Post.objects.create(run=run, visibility=Post.Visibility.PUBLIC)

    def test_reaction_option_a_change_and_remove(self):
        ok = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(ok)

        #LOVE
        resp = self.client.post(f"/posts/{self.post.id}/react/", {"reaction_type": "LOVE"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Reaction.objects.filter(post=self.post, user=self.user).exists())
        self.assertEqual(
            Reaction.objects.get(post=self.post, user=self.user).reaction_type,
            Reaction.ReactionType.LOVE,
        )
        self.assertEqual(Reaction.objects.filter(post=self.post, user=self.user).count(), 1)

        #Switch to LIKE (should replace)
        resp = self.client.post(f"/posts/{self.post.id}/react/", {"reaction_type": "LIKE"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Reaction.objects.filter(post=self.post, user=self.user).count(), 1)
        self.assertEqual(
            Reaction.objects.get(post=self.post, user=self.user).reaction_type,
            Reaction.ReactionType.LIKE,
        )

        #LIKE again should remove
        resp = self.client.post(f"/posts/{self.post.id}/react/", {"reaction_type": "LIKE"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Reaction.objects.filter(post=self.post, user=self.user).count(), 0)

class PublishPostTests(TestCase):
    def setUp(self):
        self.client = Client()
