from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404

from quests.models import QuestRun
from .models import Post

# Create your views here.


@login_required
def publish_post(request):
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

    if run.status != QuestRun.Status.COMPLETED:
        return JsonResponse(
            {"error": "Run must be COMPLETED before it can be published as a post"},
            status=400,
        )

    # Enforce "one run → max one post"
    if hasattr(run, "post"):
        return JsonResponse(
            {"error": "A post already exists for this run", "post_id": run.post.id},
            status=409,
        )

    post = Post.objects.create(run=run, visibility=Post.Visibility.PUBLIC)

    return JsonResponse(
        {
            "post_id": post.id,
            "visibility": post.visibility,
            "created_at": post.created_at.isoformat(),
            "run": {
                "id": run.id,
                "quest": run.quest.name,
                "city": run.city.name,
                "note": run.note,
                "proof_file": run.proof_file.url if run.proof_file else None,
                "time_minutes": run.time_minutes,
                "distance_km": None if run.distance_km is None else str(run.distance_km),
                "steps": run.steps,
            },
        },
        status=201,
    )

@login_required
def post_feed(request):
    # Require city selection so the feed is city-scoped
    if request.user.selected_city is None:
        return HttpResponseBadRequest("selected_city is not set for this user")

    # Pagination
    limit_raw = (request.GET.get("limit") or "20").strip()
    offset_raw = (request.GET.get("offset") or "0").strip()

    try:
        limit = min(int(limit_raw), 100)
        offset = max(int(offset_raw), 0)
    except ValueError:
        return HttpResponseBadRequest("limit and offset must be integers")

    qs = (
        Post.objects
        .filter(
            visibility=Post.Visibility.PUBLIC,
            run__city=request.user.selected_city,
        )
        .select_related("run__user", "run__quest", "run__city")
        .order_by("-created_at")
    )

    total = qs.count()
    posts = qs[offset: offset + limit]

    results = []
    for p in posts:
        run = p.run
        results.append({
            "post_id": p.id,
            "created_at": p.created_at.isoformat(),
            "visibility": p.visibility,
            "user": {"username": run.user.username},
            "city": {"id": run.city.id, "name": run.city.name},
            "quest": {
                "id": run.quest.id,
                "name": run.quest.name,
                "type": run.quest.type,
                "duration": run.quest.duration,
            },
            "run": {
                "id": run.id,
                "status": run.status,
                "group_size": run.group_size,
                "time_minutes": run.time_minutes,
                "distance_km": None if run.distance_km is None else str(run.distance_km),
                "steps": run.steps,
                "note": run.note,
                "proof_file": run.proof_file.url if run.proof_file else None,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            }
        })

    return JsonResponse({
        "meta": {
            "city": {"id": request.user.selected_city.id, "name": request.user.selected_city.name},
            "limit": limit,
            "offset": offset,
            "total": total,
        },
        "results": results,
    })