from django.contrib import admin
from .models import ItemEstoque, MovimentoEstoque


@admin.register(ItemEstoque)
class ItemEstoqueAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "quantidade_atual", "estoque_minimo", "validade")
    list_filter = ("categoria",)
    search_fields = ("nome", "fornecedor")


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("item", "data", "tipo", "quantidade", "lote_relacionado")
    list_filter = ("tipo", "data")
    search_fields = ("item__nome", "observacoes")
