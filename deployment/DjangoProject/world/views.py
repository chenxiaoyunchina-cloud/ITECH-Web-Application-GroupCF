from django.http import JsonResponse
from .models import City
from decimal import Decimal, InvalidOperation
from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404

from accounts.models import User
from .services.geocode import search_city_candidates, geocode_city_best_match


#Helper -- Used chat for this integration
def _is_moderator(user) -> bool:
    return getattr(user, "role", None) in ("MODERATOR", "ADMIN") or getattr(user, "is_staff", False)
##########################################
def city_list(request):
    cities = list(
        City.objects.all()
        .order_by("name")
        .values("id", "name", "lat", "long")
    )
    return JsonResponse(cities, safe=False)

#########Chat section##########
@login_required
def city_search(request):
    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    q = (request.GET.get("q") or "").strip()
    if not q:
        return HttpResponseBadRequest("q is required (e.g. /cities/search/?q=glasgow)")

    candidates = search_city_candidates(q, limit=5)
    return JsonResponse({
        "query": q,
        "count": len(candidates),
        "results": [
            {
                "display_name": c.display_name,
                "lat": c.lat,
                "long": c.lon,
                "place_id": c.place_id,
            }
            for c in candidates
        ]
    })

@login_required
def city_add(request):
    # Restrict to mod/admin so random users cannot add cities
    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    name = (request.POST.get("name") or "").strip()
    if not name:
        return HttpResponseBadRequest("name is required")

    # If UI posts lat/long from the chosen candidate, we do not need to call Nominatim again
    lat_raw = (request.POST.get("lat") or "").strip()
    long_raw = (request.POST.get("long") or "").strip()

    if not lat_raw or not long_raw:
        best = geocode_city_best_match(name)
        if not best:
            return JsonResponse({"error": "No geocoding match found for this city name"}, status=404)
        lat_raw = best.lat
        long_raw = best.lon

    # Avoid duplicates by name (case-insensitive)
    existing = City.objects.filter(name__iexact=name).first()
    if existing:
        return JsonResponse({
            "created": False,
            "city": {"id": existing.id, "name": existing.name, "lat": str(existing.lat), "long": str(existing.long)},
            "message": "City already exists",
        }, status=200)

    try:
        lat = Decimal(lat_raw)
        lon = Decimal(long_raw)
    except InvalidOperation:
        return HttpResponseBadRequest("lat/long must be valid numbers")

    city = City.objects.create(name=name, lat=lat, long=lon)

    return JsonResponse({
        "created": True,
        "city": {"id": city.id, "name": city.name, "lat": str(city.lat), "long": str(city.long)},
    }, status=201)

@login_required
def city_manage(request):
    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)
    return render(request, "world/city_manage.html")