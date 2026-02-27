from django.http import JsonResponse
from .models import City


def city_list(request):
    cities = list(
        City.objects.all()
        .order_by("name")
        .values("id", "name", "lat", "long")
    )
    return JsonResponse(cities, safe=False)