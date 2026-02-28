from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("me/city/", views.select_city, name="select_city"),
]