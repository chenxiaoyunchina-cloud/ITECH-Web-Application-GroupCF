from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),

    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=views.LoginForm,
        ),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("me/", views.me, name="me"),
    path("me/city/", views.select_city, name="select_city"),
]