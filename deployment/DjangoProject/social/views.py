from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from quests.models import QuestRun
from .models import Post, Comment, Reaction

#Create your views here.

def _is_moderator(user) -> bool:
    #custom user has a role field; treat MODERATOR/ADMIN as elevated.
    return getattr(user, "role", None) in ("MODERATOR", "ADMIN") or getattr(user, "is_staff", False)

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

    #Enforce "one run → max one post"
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
    #Require city selection so the feed is city-scoped
    if request.user.selected_city is None:
        return HttpResponseBadRequest("selected_city is not set for this user")

    #Pagination
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
        .annotate(
            comment_count=Count(
                "comments",
                filter=Q(comments__visibility=Comment.Visibility.PUBLIC),
                distinct=True,
            )
        )
        .order_by("-created_at")
    )

    total = qs.count()
    posts = qs[offset: offset + limit]

    post_ids = [p.id for p in posts]

    #counts per post per reaction type
    rows = (
        Reaction.objects
        .filter(post_id__in=post_ids)
        .values("post_id", "reaction_type")
        .annotate(count=Count("id"))
    )

    reaction_counts_by_post = {}
    for r in rows:
        reaction_counts_by_post.setdefault(r["post_id"], {})[r["reaction_type"]] = r["count"]

    my_reaction_by_post = dict(
        Reaction.objects
        .filter(post_id__in=post_ids, user=request.user)
        .values_list("post_id", "reaction_type")
    )

    liked_ids = set(
        Reaction.objects.filter(
            post_id__in=post_ids,
            user=request.user,
            reaction_type=Reaction.ReactionType.LIKE,
        ).values_list("post_id", flat=True)
    )

    results = []
    for p in posts:
        run = p.run
        counts = reaction_counts_by_post.get(p.id, {})
        like_count = counts.get("LIKE", 0)
        total_reactions = sum(counts.values())
        results.append({
            "post_id": p.id,
            "created_at": p.created_at.isoformat(),
            "visibility": p.visibility,
            "user": {"username": run.user.username},
            "comment_count": p.comment_count,
            "reaction_counts": counts,
            "my_reaction": my_reaction_by_post.get(p.id),
            "like_count": like_count,
            "reaction_total": total_reactions,
            "liked_by_me": p.id in liked_ids,
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

@login_required
def post_comments(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id)

    #For now: only allow comments on PUBLIC posts
    if post.visibility != Post.Visibility.PUBLIC:
        return JsonResponse({"error": "Post is not public"}, status=404)

    if request.method == "GET":
        qs = (
            Comment.objects
            .filter(post=post, visibility=Comment.Visibility.PUBLIC)
            .select_related("user")
            .order_by("created_at")
        )

        results = [{
            "comment_id": c.id,
            "created_at": c.created_at.isoformat(),
            "user": {"username": c.user.username},
            "text": c.text,
        } for c in qs]

        return JsonResponse({
            "post_id": post.id,
            "count": len(results),
            "results": results,
        })

    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        if not text:
            return JsonResponse({"error": "text is required"}, status=400)

        c = Comment.objects.create(
            post=post,
            user=request.user,
            text=text,
            visibility=Comment.Visibility.PUBLIC,
        )

        return JsonResponse({
            "comment_id": c.id,
            "created_at": c.created_at.isoformat(),
            "user": {"username": c.user.username},
            "text": c.text,
        }, status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@login_required
def toggle_like(request, post_id: int):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    # reusing set_reaction behavior: LIKE toggles on/off
    request.POST = request.POST.copy()
    request.POST["reaction_type"] = "LIKE"
    return set_reaction(request, post_id)

@login_required
def post_reactions(request, post_id: int):
    if request.method != "GET":
        return JsonResponse({"error": "GET required"}, status=405)

    post = get_object_or_404(Post, pk=post_id, visibility=Post.Visibility.PUBLIC)

    #counts per reaction_type
    rows = (
        Reaction.objects
        .filter(post=post)
        .values("reaction_type")
        .annotate(count=Count("id"))
    )
    counts = {r["reaction_type"]: r["count"] for r in rows}

    #my reaction (single choice)
    my_reaction = (
        Reaction.objects
        .filter(post=post, user=request.user)
        .values_list("reaction_type", flat=True)
        .first()
    )

    return JsonResponse({
        "post_id": post.id,
        "counts": counts,
        "my_reaction": my_reaction,
        "total": sum(counts.values()),
    })

@login_required
def set_reaction(request, post_id: int):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    post = get_object_or_404(Post, pk=post_id, visibility=Post.Visibility.PUBLIC)

    reaction_type = (request.POST.get("reaction_type") or "").strip().upper()
    if not reaction_type:
        return JsonResponse({"error": "reaction_type is required"}, status=400)

    valid = {c[0] for c in Reaction.ReactionType.choices}
    if reaction_type not in valid:
        return JsonResponse({"error": f"Invalid reaction_type. Use one of: {sorted(valid)}"}, status=400)

    existing = Reaction.objects.filter(post=post, user=request.user).first()

    if existing and existing.reaction_type == reaction_type:
        existing.delete()
        my_reaction = None
    else:
        if existing:
            existing.reaction_type = reaction_type
            existing.save(update_fields=["reaction_type"])
        else:
            Reaction.objects.create(post=post, user=request.user, reaction_type=reaction_type)
        my_reaction = reaction_type

    counts_qs = (
        Reaction.objects
        .filter(post=post)
        .values("reaction_type")
        .annotate(count=Count("id"))
    )
    counts = {row["reaction_type"]: row["count"] for row in counts_qs}

    return JsonResponse({
        "post_id": post.id,
        "my_reaction": my_reaction,
        "counts": counts,
    })

@login_required
def set_post_visibility(request, post_id: int):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    post = get_object_or_404(Post, pk=post_id)

    #owner is the user who did the run that generated this post
    is_owner = (post.run.user_id == request.user.id)
    if not (is_owner or _is_moderator(request.user)):
        return JsonResponse({"error": "Forbidden"}, status=403)

    visibility = (request.POST.get("visibility") or "").strip().upper()
    valid = {c[0] for c in Post.Visibility.choices}
    if visibility not in valid:
        return JsonResponse({"error": f"Invalid visibility. Use one of: {sorted(valid)}"}, status=400)

    post.visibility = visibility
    post.save(update_fields=["visibility"])

    return JsonResponse({
        "post_id": post.id,
        "visibility": post.visibility,
    })

@login_required
def set_comment_visibility(request, comment_id: int):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    comment = get_object_or_404(Comment, pk=comment_id)

    is_owner = (comment.user_id == request.user.id)
    if not (is_owner or _is_moderator(request.user)):
        return JsonResponse({"error": "Forbidden"}, status=403)

    visibility = (request.POST.get("visibility") or "").strip().upper()
    valid = {c[0] for c in Comment.Visibility.choices}
    if visibility not in valid:
        return JsonResponse({"error": f"Invalid visibility. Use one of: {sorted(valid)}"}, status=400)

    comment.visibility = visibility
    comment.save(update_fields=["visibility"])

    return JsonResponse({
        "comment_id": comment.id,
        "post_id": comment.post_id,
        "visibility": comment.visibility,
    })

@login_required
def my_posts(request):
    limit_raw = (request.GET.get("limit") or "20").strip()
    offset_raw = (request.GET.get("offset") or "0").strip()
    try:
        limit = min(int(limit_raw), 100)
        offset = max(int(offset_raw), 0)
    except ValueError:
        return HttpResponseBadRequest("limit and offset must be integers")

    qs = (
        Post.objects
        .filter(run__user=request.user)  #all my posts, regardless of visibility
        .select_related("run__quest", "run__city")
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
            "city": {"id": run.city.id, "name": run.city.name},
            "quest": {"id": run.quest.id, "name": run.quest.name, "type": run.quest.type},
            "run_id": run.id,
        })

    return JsonResponse({
        "meta": {"limit": limit, "offset": offset, "total": total},
        "results": results,
    })

