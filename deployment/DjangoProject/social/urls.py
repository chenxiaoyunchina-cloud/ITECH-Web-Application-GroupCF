from django.urls import path
from . import views

app_name = "social"

urlpatterns = [
    path("posts/", views.post_feed, name="post_feed"),
    path("posts/publish/", views.publish_post, name="publish_post"),
    path("posts/<int:post_id>/comments/", views.post_comments, name="post_comments"),
    path("posts/<int:post_id>/like/", views.toggle_like, name="toggle_like"),
    path("posts/<int:post_id>/react/", views.set_reaction, name="set_reaction"),
    path("posts/<int:post_id>/reactions/", views.post_reactions, name="post_reactions"),
    path("posts/<int:post_id>/visibility/", views.set_post_visibility, name="set_post_visibility"),
    path("comments/<int:comment_id>/visibility/", views.set_comment_visibility, name="set_comment_visibility"),
    path("my/posts/", views.my_posts, name="my_posts"),
]