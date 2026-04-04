from django.contrib import admin
from .models import Abate


@admin.register(Abate)
class AbateAdmin(admin.ModelAdmin):
    list_display = ("data", "lote", "quantidade_abatida", "peso_total", "receita_gerada")
    list_filter = ("data",)
    search_fields = ("lote__nome",)
