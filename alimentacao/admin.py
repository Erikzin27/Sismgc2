from django.contrib import admin
from .models import FormulaRacao


@admin.register(FormulaRacao)
class FormulaRacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "fase", "custo_total")
    list_filter = ("fase",)
    search_fields = ("nome",)
