from django.contrib import admin
from .models import RegistroGenetico


@admin.register(RegistroGenetico)
class RegistroGeneticoAdmin(admin.ModelAdmin):
    list_display = ("filho", "pai", "mae", "created_at")
    search_fields = ("filho__codigo_interno", "pai__codigo_interno", "mae__codigo_interno")
