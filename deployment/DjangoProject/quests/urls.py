from django.urls import path
from . import views

app_name = "quests"

urlpatterns = [
    path("quests/recommend/", views.recommend_quest, name="recommend_quest"),
    path("quests/shuffle/", views.shuffle_quest, name="shuffle_quest"),
    path("quests/start/", views.start_quest, name="start_quest"),
    path("quests/complete/", views.complete_quest, name="complete_quest"),
]