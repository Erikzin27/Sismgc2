from django.shortcuts import render, redirect
from django.contrib import messages


def permission_denied_view(request, exception=None):
    messages.warning(request, "Você não tem permissão para acessar esta área.")
    return render(request, "403.html", status=403)
