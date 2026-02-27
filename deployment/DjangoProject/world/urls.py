from django.urls import path
from . import views

app_name = "world"

urlpatterns = [
    path("cities/", views.city_list, name="city_list"),
]