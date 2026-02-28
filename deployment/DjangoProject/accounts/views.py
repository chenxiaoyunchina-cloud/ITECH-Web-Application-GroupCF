# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from world.models import City


@login_required
def select_city(request):
    if request.method == "POST":
        city_id = request.POST.get("city_id", "").strip()
        if not city_id:
            return HttpResponseBadRequest("city_id is required")

        try:
            city_id_int = int(city_id)
        except ValueError:
            return HttpResponseBadRequest("city_id must be an integer")

        city = get_object_or_404(City, pk=city_id_int)
        request.user.selected_city = city
        request.user.save(update_fields=["selected_city"])
        return redirect("accounts:select_city")

    cities = City.objects.all().order_by("name")
    return render(
        request,
        "accounts/select_city.html",
        {"cities": cities, "selected_city": request.user.selected_city},
    )