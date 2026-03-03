import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import QuestTemplate, QuestRun


@login_required
def recommend_quest(request):
    #REQUIRE city selection first
    if request.user.selected_city is None:
        return HttpResponseBadRequest("selected_city is not set for this user")

    #group_size is required
    group_size_raw = (request.GET.get("group_size") or "").strip()
    if not group_size_raw:
        return HttpResponseBadRequest("group_size is required (e.g. ?group_size=3)")

    try:
        group_size = int(group_size_raw)
    except ValueError:
        return HttpResponseBadRequest("group_size must be an integer")

    #quest type filter (WALK/CYCLE/TRANSIT/MIXED)
    qtype = (request.GET.get("type") or "").strip().upper()

    qs = QuestTemplate.objects.filter(is_active=True)

    #if type is provided, accept that type OR MIXED
    if qtype:
        qs = qs.filter(type__in=[qtype, QuestTemplate.QuestType.MIXED])

    #Apply group size filter (using the helper on the model)
    candidates = [q for q in qs.order_by("id") if q.fits_group_size(group_size)]

    if not candidates:
        return JsonResponse(
            {"error": "No quests match the given criteria"},
            status=404
        )

    quest = random.choice(candidates)

    #Store the last recommendation so we can implement shuffle next
    request.session["last_recommended_quest_id"] = quest.id
    request.session["last_recommend_group_size"] = group_size
    request.session["last_recommend_type"] = qtype

    return JsonResponse(
        {
            "id": quest.id,
            "name": quest.name,
            "description": quest.description,
            "type": quest.type,
            "group_limits": quest.group_limits,
            "duration": quest.duration,
            "selected_city": None if not request.user.selected_city else request.user.selected_city.name,
        }
    )
@login_required
def shuffle_quest(request):
    if request.user.selected_city is None:
        return HttpResponseBadRequest("selected_city is not set for this user")

    #use last recommendation criteria by default
    last_id = request.session.get("last_recommended_quest_id")
    group_size = request.session.get("last_recommend_group_size")
    qtype = request.session.get("last_recommend_type") or ""

    #Allow override if you pass params
    group_size_raw = (request.GET.get("group_size") or "").strip()
    if group_size_raw:
        try:
            group_size = int(group_size_raw)
        except ValueError:
            return HttpResponseBadRequest("group_size must be an integer")

    qtype_override = (request.GET.get("type") or "").strip().upper()
    if qtype_override:
        qtype = qtype_override

    if group_size is None:
        return HttpResponseBadRequest("No previous recommendation. Call /quests/recommend/?group_size=... first.")

    qs = QuestTemplate.objects.filter(is_active=True)

    if qtype:
        qs = qs.filter(type__in=[qtype, QuestTemplate.QuestType.MIXED])

    candidates = [q for q in qs.order_by("id") if q.fits_group_size(group_size)]

    if not candidates:
        return JsonResponse({"error": "No quests match the given criteria"}, status=404)

    #Exclude last recommended quest if possible
    if last_id is not None:
        candidates_excluding_last = [q for q in candidates if q.id != last_id]
    else:
        candidates_excluding_last = candidates

    if candidates_excluding_last:
        quest = random.choice(candidates_excluding_last)
        shuffled = True
    else:
        #if there is only one quest available; return the same one
        quest = candidates[0]
        shuffled = False

    request.session["last_recommended_quest_id"] = quest.id
    request.session["last_recommend_group_size"] = group_size
    request.session["last_recommend_type"] = qtype

    return JsonResponse(
        {
            "id": quest.id,
            "name": quest.name,
            "description": quest.description,
            "type": quest.type,
            "group_limits": quest.group_limits,
            "duration": quest.duration,
            "selected_city": request.user.selected_city.name,
            "shuffled": shuffled,
        }
    )

@login_required
def start_quest(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    if request.user.selected_city is None:
        return HttpResponseBadRequest("selected_city is not set for this user")

    quest_id_raw = (request.POST.get("quest_id") or "").strip()
    group_size_raw = (request.POST.get("group_size") or "").strip()

    if not quest_id_raw:
        return HttpResponseBadRequest("quest_id is required")
    if not group_size_raw:
        return HttpResponseBadRequest("group_size is required")

    try:
        quest_id = int(quest_id_raw)
        group_size = int(group_size_raw)
    except ValueError:
        return HttpResponseBadRequest("quest_id and group_size must be integers")

    quest = get_object_or_404(QuestTemplate, pk=quest_id, is_active=True)

    #enforce group_limits at start time
    if not quest.fits_group_size(group_size):
        return JsonResponse(
            {"error": f"group_size {group_size} does not fit quest group_limits {quest.group_limits}"},
            status=400,
        )

    run = QuestRun.objects.create(
        user=request.user,
        quest=quest,
        city=request.user.selected_city,
        group_size=group_size,
        status=QuestRun.Status.IN_PROGRESS,
    )

    return JsonResponse(
        {
            "run_id": run.id,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "quest": {
                "id": quest.id,
                "name": quest.name,
                "type": quest.type,
                "duration": quest.duration,
            },
            "city": {
                "id": run.city.id,
                "name": run.city.name,
            },
        },
        status=201,
    )

@login_required
def complete_quest(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    run_id_raw = (request.POST.get("run_id") or "").strip()
    if not run_id_raw:
        return HttpResponseBadRequest("run_id is required")

    try:
        run_id = int(run_id_raw)
    except ValueError:
        return HttpResponseBadRequest("run_id must be an integer")

    run = get_object_or_404(QuestRun, pk=run_id, user=request.user)

    if run.status != QuestRun.Status.IN_PROGRESS:
        return JsonResponse(
            {"error": f"Run is not in progress (current status: {run.status})"},
            status=400,
        )

    note = request.POST.get("note", "")
    time_minutes = request.POST.get("time_minutes", "").strip()
    distance_km = request.POST.get("distance_km", "").strip()
    steps = request.POST.get("steps", "").strip()

    #parsing numeric fields safely
    if time_minutes:
        try:
            run.time_minutes = int(time_minutes)
        except ValueError:
            return HttpResponseBadRequest("time_minutes must be an integer")

    if distance_km:
        try:
            run.distance_km = distance_km  #DecimalField accepts string
        except Exception:
            return HttpResponseBadRequest("distance_km must be a number (e.g. 2.50)")

    if steps:
        try:
            run.steps = int(steps)
        except ValueError:
            return HttpResponseBadRequest("steps must be an integer")

    run.note = note
    run.status = QuestRun.Status.COMPLETED
    run.completed_at = timezone.now()

    proof = request.FILES.get("proof_file")
    if proof is not None:
        run.proof_file = proof = proof

    run.save()

    return JsonResponse(
        {
            "run_id": run.id,
            "status": run.status,
            "completed_at": run.completed_at.isoformat(),
            "time_minutes": run.time_minutes,
            "distance_km": None if run.distance_km is None else str(run.distance_km),
            "steps": run.steps,
            "note": run.note,
            "proof_file": run.proof_file.url if run.proof_file else None,
        }
    )