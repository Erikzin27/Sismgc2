from django.contrib import admin
from .models import Linhagem


@admin.register(Linhagem)
class LinhagemAdmin(admin.ModelAdmin):
    list_display = ("nome", "origem", "ativo", "created_at")
    list_filter = ("ativo",)
    search_fields = ("nome", "origem")
