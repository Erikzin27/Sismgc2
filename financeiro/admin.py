from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import LancamentoFinanceiro, OrcamentoFuturo


def _venda_link_html(obj):
    """Exibe link para a venda if exists."""
    if obj.venda:
        url = reverse('admin:vendas_venda_change', args=[obj.venda.pk])
        return format_html(
            '<a href="{}" target="_blank">Venda #{} - {}</a>',
            url,
            obj.venda.pk,
            obj.venda.cliente
        )
    else:
        return format_html('<span style="color: gray;">Manual</span>')

_venda_link_html.short_description = "Origem"


@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("data", "tipo", "categoria", _venda_link_html, "valor", "forma_pagamento")
    list_filter = ("tipo", "categoria", "data")
    search_fields = ("descricao", "venda__cliente")
    readonly_fields = ("created_at", "updated_at", "venda_link", "tipo", "categoria")
    fieldsets = (
        ("Informações do Lançamento", {
            "fields": ("data", "tipo", "categoria", "descricao", "valor")
        }),
        ("Relacionamentos", {
            "fields": ("lote", "ave", "venda_link")
        }),
        ("Pagamento", {
            "fields": ("forma_pagamento", "observacoes", "comprovante")
        }),
        ("Auditoria", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def venda_link(self, obj):
        """Mostra link para a venda vinculada."""
        if obj.venda:
            url = reverse('admin:vendas_venda_change', args=[obj.venda.pk])
            return format_html(
                '<a href="{}" target="_blank">Ver venda #{} de {} (R$ {})</a>',
                url,
                obj.venda.pk,
                obj.venda.cliente,
                obj.venda.valor_total
            )
        else:
            return format_html(
                '<span style="color: gray;">Lançamento manual (não vinculado a nenhuma venda)</span>'
            )

    venda_link.short_description = "Venda Vinculada"

    def has_add_permission(self, request):
        """Impede criar lançamentos manuais vindos do admin se forem vendas."""
        # Permitir criar mas avisar que devem usar o módulo de vendas
        return True

    def get_readonly_fields(self, request, obj=None):
        """Se tiver venda vinculada, mostra campos como read-only."""
        readonly = super().get_readonly_fields(request, obj)
        if obj and obj.venda:
            # Impede editar campos críticos se foi gerado automaticamente por venda
            return tuple(readonly) + ("data", "tipo", "categoria", "valor")
        return readonly


@admin.register(OrcamentoFuturo)
class OrcamentoFuturoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status", "prioridade", "valor_previsto", "data_planejada", "ativo")
    list_filter = ("status", "prioridade", "ativo", "data_planejada")
    search_fields = ("titulo", "descricao", "categoria")
