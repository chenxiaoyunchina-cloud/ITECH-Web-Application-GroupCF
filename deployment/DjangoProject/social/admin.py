from django.contrib import admin
from .models import Post, Comment

# Register your models here.


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "run", "visibility", "created_at")
    list_filter = ("visibility",)
    search_fields = ("run__user__username", "run__quest__name", "run__city__name")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "visibility", "created_at")
    list_filter = ("visibility",)
    search_fields = ("user__username", "post__run__quest__name", "post__run__city__name")