from django.urls import path
from . import views

app_name = "social"

urlpatterns = [
    path("posts/", views.post_feed, name="post_feed"),
    path("posts/publish/", views.publish_post, name="publish_post"),
]