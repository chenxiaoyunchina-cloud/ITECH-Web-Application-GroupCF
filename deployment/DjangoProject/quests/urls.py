from django.urls import path
from . import views

app_name = "quests"

urlpatterns = [
    path("quest-board/", views.shuffle_page, name="shuffle_page"),
    path("quest-progress/", views.quest_progress_page, name="quest_progress_page"),
    path("quest-complete/", views.quest_complete_page, name="quest_complete_page"),
    
    path("recommend/", views.recommend_quest, name="recommend_quest"),
    path("shuffle/", views.shuffle_quest, name="shuffle_quest"),
    path("start/", views.start_quest, name="start_quest"),
    path("complete/", views.complete_quest, name="complete_quest"),
]