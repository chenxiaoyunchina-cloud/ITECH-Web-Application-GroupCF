from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User
# Register your models here.

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "selected_city", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("SideQuest City", {"fields": ("role", "selected_city")}),
    )

    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("SideQuest City", {"fields": ("email", "role", "selected_city")}),
    )