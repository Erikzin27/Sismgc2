from django.contrib import admin
from .models import Ave


@admin.register(Ave)
class AveAdmin(admin.ModelAdmin):
    list_display = ("codigo_interno", "linhagem", "sexo", "finalidade", "lote_atual", "status", "ativo")
    list_filter = ("finalidade", "sexo", "status", "ativo", "linhagem")
    search_fields = ("codigo_interno", "identificacao", "nome")
