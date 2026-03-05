from django.urls import path
from . import views

app_name = "world"

urlpatterns = [
    path("cities/", views.city_list, name="city_list"),
    path("cities/search/", views.city_search, name="city_search"),
    path("cities/add/", views.city_add, name="city_add"),
    path("cities/manage/", views.city_manage, name="city_manage"),
]