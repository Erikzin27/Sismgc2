from django.contrib import admin
from .models import LancamentoFinanceiro, OrcamentoFuturo


@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("data", "tipo", "categoria", "descricao", "valor")
    list_filter = ("tipo", "categoria")
    search_fields = ("descricao",)


@admin.register(OrcamentoFuturo)
class OrcamentoFuturoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status", "prioridade", "valor_previsto", "data_planejada", "ativo")
    list_filter = ("status", "prioridade", "ativo")
    search_fields = ("titulo", "descricao", "categoria")
