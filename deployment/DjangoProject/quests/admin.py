from django.contrib import admin
from .models import QuestTemplate, QuestRun
# Register your models here.

@admin.register(QuestTemplate)
class QuestTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "group_limits", "duration", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)

@admin.register(QuestRun)
class QuestRunAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quest", "city", "status", "started_at", "completed_at")
    list_filter = ("status", "city")
    search_fields = ("user__username", "quest__name", "city__name")