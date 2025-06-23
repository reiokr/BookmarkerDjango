from smtplib import SMTPResponseException

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.


def index(request, *args, **kwargs):
    data = {"title": "Bookmarker"}
    if request.session.session_key != None:
        context = {'data': data}
    return HttpResponse(data)
