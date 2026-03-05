from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from world.models import City
from pins.services.wikivoyage import fetch_city_wikitext, extract_places_from_wikitext
from urllib.parse import quote_plus

from .models import Pin, PinReport

# Create your views here

#role helper
def _is_moderator(user) -> bool:
    return getattr(user, "role", None) in ("MODERATOR", "ADMIN") or getattr(user, "is_staff", False)

@login_required
def seed_wikivoyage_pins(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    #explicit city_id or fallback to user's selected_city
    city_id_raw = (request.POST.get("city_id") or "").strip()
    if city_id_raw:
        try:
            city_id = int(city_id_raw)
        except ValueError:
            return HttpResponseBadRequest("city_id must be an integer")
        city = get_object_or_404(City, pk=city_id)
    else:
        if request.user.selected_city is None:
            return HttpResponseBadRequest("selected_city is not set for this user")
        city = request.user.selected_city

    limit_raw = (request.POST.get("limit") or "50").strip()
    refresh_raw = (request.POST.get("refresh") or "false").strip().lower()
    page_title = (request.POST.get("page_title") or "").strip() or city.name

    try:
        limit = min(max(int(limit_raw), 1), 200)
    except ValueError:
        return HttpResponseBadRequest("limit must be an integer")

    refresh = refresh_raw in ("1", "true", "yes", "y", "on")

    try:
        wikitext = fetch_city_wikitext(page_title)
        places = extract_places_from_wikitext(page_title, wikitext, limit=limit)
    except Exception as e:
        return JsonResponse({"error": f"Wikivoyage fetch/parse failed: {e}"}, status=400)

    if not places:
        return JsonResponse({"error": "No mappable listings found for this city/page_title"}, status=404)

    created = 0
    skipped = 0
    deleted = 0

    with transaction.atomic():
        if refresh:
            deleted, _ = Pin.objects.filter(city=city, is_seeded=True).delete()

        for place in places:
            exists = Pin.objects.filter(
                city=city,
                is_seeded=True,
                title=place.title,
                lat=place.lat,
                long=place.long,
            ).exists()
            if exists:
                skipped += 1
                continue

            Pin.objects.create(
                city=city,
                user=request.user,
                title=place.title,
                description=place.description,
                lat=place.lat,
                long=place.long,
                status=Pin.Status.APPROVED,
                source_url=place.source_url,
                is_seeded=True,
            )
            created += 1

    return JsonResponse({
        "city": {"id": city.id, "name": city.name},
        "page_title": page_title,
        "limit": limit,
        "refresh": refresh,
        "deleted_seeded": deleted,
        "created": created,
        "skipped_duplicates": skipped,
    }, status=201)

@login_required
def pin_list(request):
    if request.user.selected_city is None:
        return HttpResponseBadRequest("selected_city is not set for this user")

    qs = (
        Pin.objects
        .filter(
            city=request.user.selected_city,
            status=Pin.Status.APPROVED,
        )
        .select_related("city", "user")
        .order_by("-created_at")
    )

    results = []
    for p in qs:
        results.append({
            "pin_id": p.id,
            "title": p.title,
            "description": p.description,
            "lat": str(p.lat),
            "long": str(p.long),
            "source_url": p.source_url or None,
            "is_seeded": p.is_seeded,
            "city": {"id": p.city.id, "name": p.city.name},
            "created_by": {"username": p.user.username},
            "created_at": p.created_at.isoformat(),
        })

    return JsonResponse({
        "city": {"id": request.user.selected_city.id, "name": request.user.selected_city.name},
        "count": len(results),
        "results": results,
    })

@login_required
def submit_pin(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    if request.user.selected_city is None:
        return HttpResponseBadRequest("selected_city is not set for this user")

    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    lat_raw = (request.POST.get("lat") or "").strip()
    long_raw = (request.POST.get("long") or "").strip()

    if not title:
        return HttpResponseBadRequest("title is required")
    if not lat_raw or not long_raw:
        return HttpResponseBadRequest("lat and long are required")

    try:
        lat = float(lat_raw)
        lon = float(long_raw)
    except ValueError:
        return HttpResponseBadRequest("lat and long must be numbers")

    #sanity checks
    if not (-90 <= lat <= 90):
        return HttpResponseBadRequest("lat must be between -90 and 90")
    if not (-180 <= lon <= 180):
        return HttpResponseBadRequest("long must be between -180 and 180")

    pin = Pin.objects.create(
        city=request.user.selected_city,
        user=request.user,
        title=title,
        description=description,
        lat=lat,
        long=lon,
        status=Pin.Status.PENDING,
    )

    return JsonResponse(
        {
            "pin_id": pin.id,
            "status": pin.status,
            "city": {"id": pin.city.id, "name": pin.city.name},
            "title": pin.title,
            "description": pin.description,
            "lat": str(pin.lat),
            "long": str(pin.long),
            "created_at": pin.created_at.isoformat(),
        },
        status=201,
    )

@login_required
def pending_pins(request):
    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    #city filter
    city_id_raw = (request.GET.get("city_id") or "").strip()

    qs = Pin.objects.filter(status=Pin.Status.PENDING).select_related("city", "user").order_by("-created_at")

    if city_id_raw:
        try:
            city_id = int(city_id_raw)
        except ValueError:
            return HttpResponseBadRequest("city_id must be an integer")
        qs = qs.filter(city_id=city_id)

    results = []
    for p in qs:
        results.append({
            "pin_id": p.id,
            "title": p.title,
            "description": p.description,
            "lat": str(p.lat),
            "long": str(p.long),
            "status": p.status,
            "city": {"id": p.city.id, "name": p.city.name},
            "submitted_by": {"username": p.user.username},
            "created_at": p.created_at.isoformat(),
        })

    return JsonResponse({"count": len(results), "results": results})

@login_required
def set_pin_status(request, pin_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    pin = get_object_or_404(Pin, pk=pin_id)

    status = (request.POST.get("status") or "").strip().upper()
    allowed = {Pin.Status.APPROVED, Pin.Status.REJECTED}

    if status not in allowed:
        return JsonResponse({"error": f"status must be one of: {sorted(allowed)}"}, status=400)

    pin.status = status
    pin.save(update_fields=["status"])

    return JsonResponse({
        "pin_id": pin.id,
        "status": pin.status,
    })

@login_required
def my_pins(request):
    # more filters
    city_id_raw = (request.GET.get("city_id") or "").strip()
    status_raw = (request.GET.get("status") or "").strip().upper()  # PENDING/APPROVED/REJECTED

    qs = Pin.objects.filter(user=request.user).select_related("city").order_by("-created_at")

    #if user has selected_city and no city_id given, show that city’s pins
    if city_id_raw:
        try:
            city_id = int(city_id_raw)
        except ValueError:
            return HttpResponseBadRequest("city_id must be an integer")
        qs = qs.filter(city_id=city_id)
    else:
        if request.user.selected_city is not None:
            qs = qs.filter(city=request.user.selected_city)

    if status_raw:
        allowed = {Pin.Status.PENDING, Pin.Status.APPROVED, Pin.Status.REJECTED}
        if status_raw not in allowed:
            return JsonResponse({"error": f"status must be one of: {sorted(allowed)}"}, status=400)
        qs = qs.filter(status=status_raw)

    results = []
    for p in qs:
        results.append({
            "pin_id": p.id,
            "title": p.title,
            "description": p.description,
            "lat": str(p.lat),
            "long": str(p.long),
            "status": p.status,
            "city": {"id": p.city.id, "name": p.city.name},
            "is_seeded": p.is_seeded,
            "source_url": p.source_url or None,
            "created_at": p.created_at.isoformat(),
        })

    return JsonResponse({
        "count": len(results),
        "results": results,
    })

@login_required
def pin_detail(request, pin_id: int):
    pin = get_object_or_404(Pin, pk=pin_id)

    #Access rules:
    #approved pins visible to everyone logged in
    #non-approved pins visible only to owner or moderator/admin
    if pin.status != Pin.Status.APPROVED:
        is_owner = (pin.user_id == request.user.id)
        if not (is_owner or _is_moderator(request.user)):
            return JsonResponse({"error": "Not found"}, status=404)

    #Google Maps directions link
    #link the frontend can open in a new tab/app.
    directions_url = f"https://www.google.com/maps/dir/?api=1&destination={pin.lat},{pin.long}"

    return JsonResponse({
        "pin_id": pin.id,
        "title": pin.title,
        "description": pin.description,
        "lat": str(pin.lat),
        "long": str(pin.long),
        "status": pin.status,
        "city": {"id": pin.city.id, "name": pin.city.name},
        "created_by": {"username": pin.user.username},
        "is_seeded": pin.is_seeded,
        "source_url": pin.source_url or None,
        "created_at": pin.created_at.isoformat(),
        "directions_url": directions_url,
    })

@login_required
def report_pin(request, pin_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    pin = get_object_or_404(Pin, pk=pin_id)

    if pin.status != Pin.Status.APPROVED:
        return JsonResponse({"error": "Only approved pins can be reported"}, status=400)

    reason = (request.POST.get("reason") or "").strip()
    details = (request.POST.get("details") or "").strip()

    if not reason:
        return HttpResponseBadRequest("reason is required")

    report, created = PinReport.objects.get_or_create(
        pin=pin,
        reporter=request.user,
        reason=reason[:120],
        defaults={"details": details},
    )

    if not created and details:
        #allow reporter to update details on an existing same-reason report
        report.details = details
        report.save(update_fields=["details"])

    return JsonResponse(
        {
            "report_id": report.id,
            "created": created,
            "status": report.status,
            "pin_id": pin.id,
            "reason": report.reason,
            "details": report.details,
            "created_at": report.created_at.isoformat(),
        },
        status=201 if created else 200,
    )

@login_required
def list_pin_reports(request):
    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    status_raw = (request.GET.get("status") or "OPEN").strip().upper()  #OPEN/REVIEWED/DISMISSED
    allowed = {PinReport.Status.OPEN, PinReport.Status.REVIEWED, PinReport.Status.DISMISSED}
    if status_raw not in allowed:
        return JsonResponse({"error": f"status must be one of: {sorted(allowed)}"}, status=400)

    qs = (
        PinReport.objects
        .filter(status=status_raw)
        .select_related("pin__city", "pin__user", "reporter")
        .order_by("-created_at")
    )

    results = []
    for r in qs:
        p = r.pin
        results.append({
            "report_id": r.id,
            "status": r.status,
            "reason": r.reason,
            "details": r.details,
            "created_at": r.created_at.isoformat(),
            "reporter": {"username": r.reporter.username},
            "pin": {
                "pin_id": p.id,
                "title": p.title,
                "status": p.status,
                "city": {"id": p.city.id, "name": p.city.name},
                "created_by": {"username": p.user.username},
                "lat": str(p.lat),
                "long": str(p.long),
                "source_url": p.source_url or None,
                "is_seeded": p.is_seeded,
            }
        })

    return JsonResponse({"count": len(results), "results": results})

@login_required
def set_pin_report_status(request, report_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    if not _is_moderator(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    report = get_object_or_404(PinReport, pk=report_id)

    status_raw = (request.POST.get("status") or "").strip().upper()
    allowed = {PinReport.Status.REVIEWED, PinReport.Status.DISMISSED}
    if status_raw not in allowed:
        return JsonResponse({"error": f"status must be one of: {sorted(allowed)}"}, status=400)

    report.status = status_raw
    report.save(update_fields=["status"])

    return JsonResponse({
        "report_id": report.id,
        "status": report.status,
        "pin_id": report.pin_id,
    })