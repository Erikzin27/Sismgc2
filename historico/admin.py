from django.contrib import admin
from .models import HistoricoEvento


@admin.register(HistoricoEvento)
class HistoricoEventoAdmin(admin.ModelAdmin):
    list_display = ("entidade", "acao", "referencia_id", "descricao", "usuario", "created_at")
    search_fields = ("entidade", "descricao")
    list_filter = ("acao", "entidade")
