# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login, logout
from django.views.decorators.http import require_http_methods

from world.models import City
from .forms import RegisterForm


@login_required
def select_city(request):
    if request.method == "POST":
        city_id = request.POST.get("city_id", "").strip()
        if not city_id:
            return HttpResponseBadRequest("city_id is required")

        group_size_raw = (request.POST.get("group_size") or "1").strip()
        try:
            group_size = int(group_size_raw)
        except ValueError:
            return HttpResponseBadRequest("group_size must be an integer")

        if group_size < 1 or group_size > 10:
            return HttpResponseBadRequest("group_size must be between 1 and 10")

        try:
            city_id_int = int(city_id)
        except ValueError:
            return HttpResponseBadRequest("city_id must be an integer")

        city = get_object_or_404(City, pk=city_id_int)
        request.user.selected_city = city
        request.user.save(update_fields=["selected_city"])

        request.session["group_size"] = group_size

        return redirect("accounts:select_city")

    cities = City.objects.all().order_by("name")
    return render(
        request,
        "accounts/select_city.html",
        {
            "cities": cities,
            "selected_city": request.user.selected_city,
            "selected_group_size": request.session.get("group_size", 1),
        },
    )


@login_required
def me(request):
    city = request.user.selected_city
    data = {
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email,
        "role": request.user.role,
        "group_size": request.session.get("group_size", 1),
        "selected_city": None if not city else {
            "id": city.id,
            "name": city.name,
            "lat": str(city.lat),
            "long": str(city.long),
        }
    }
    return JsonResponse(data)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # logs them in immediately
            return redirect("accounts:select_city")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect("/login/")


def home(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    if getattr(request.user, "selected_city", None) is None:
        return redirect("/me/city/")

    return redirect("quests:shuffle_page")