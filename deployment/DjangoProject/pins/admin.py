from django.contrib import admin
from .models import Pin, PinReport

# Register your models here.
@admin.register(Pin)
class PinAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "city", "user", "status", "is_seeded", "created_at")
    list_filter = ("status", "city", "is_seeded")
    search_fields = ("title", "city__name", "user__username")

@admin.register(PinReport)
class PinReportAdmin(admin.ModelAdmin):
    list_display = ("id", "pin", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "reason")
    search_fields = ("pin__title", "reporter__username")