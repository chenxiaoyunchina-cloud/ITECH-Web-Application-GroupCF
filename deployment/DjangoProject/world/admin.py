from django.contrib import admin

# Register your models here.
from .models import City

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "lat", "long")
    search_fields = ("name",)