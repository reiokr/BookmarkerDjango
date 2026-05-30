from django.http import JsonResponse


def index(request, *args, **kwargs):
    data = {"title": "Bookmarker"}
    return JsonResponse(data)
