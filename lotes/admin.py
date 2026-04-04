from django.contrib import admin
from .models import Lote


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "finalidade", "linhagem_principal", "quantidade_atual", "status")
    list_filter = ("finalidade", "status", "linhagem_principal")
    search_fields = ("nome", "codigo")
