from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Venda


def _tem_entrada_html(obj):
    """Exibe se tem entrada no financeiro com ícone."""
    if obj.tem_entrada_financeira:
        url = reverse('admin:financeiro_lancamentofinanceiro_change', args=[obj.lancamento_financeiro.pk])
        return format_html(
            '<a href="{}" target="_blank" style="color: green;"><b>✓ Vinculada</b></a>',
            url
        )
    elif obj.status_pagamento == Venda.STATUS_PAGO:
        return format_html('<span style="color: orange;"><b>⚠ Pendente</b></span>')
    else:
        return format_html('<span style="color: gray;">Sem entrada</span>')

_tem_entrada_html.short_description = "Financeiro"


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        "data",
        "cliente",
        "produto",
        "categoria",
        "valor_total",
        "status_pagamento",
        _tem_entrada_html,
    )
    list_filter = ("categoria", "status_pagamento", "data")
    search_fields = ("cliente", "produto", "codigo_interno")
    readonly_fields = ("created_at", "updated_at", "lancamento_financeiro_link", "status_integracao_display")
    fieldsets = (
        ("Informações da Venda", {
            "fields": ("data", "cliente", "produto", "categoria", "quantidade", "unidade", "valor_unitario", "desconto", "valor_total")
        }),
        ("Status e Pagamento", {
            "fields": ("status_pagamento", "forma_pagamento", "observacoes")
        }),
        ("Relacionamentos", {
            "fields": ("lote", "ave")
        }),
        ("Integração Financeira", {
            "fields": ("status_integracao_display", "lancamento_financeiro_link"),
            "description": "Mostra o status da sincronização com o módulo financeiro."
        }),
        ("Auditoria", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def lancamento_financeiro_link(self, obj):
        """Exibe link para o lançamento financeiro vinculado."""
        if obj.tem_entrada_financeira:
            url = reverse('admin:financeiro_lancamentofinanceiro_change', args=[obj.lancamento_financeiro.pk])
            return format_html(
                '<a href="{}" target="_blank">Lançamento #{}</a>',
                url,
                obj.lancamento_financeiro.pk
            )
        elif obj.status_pagamento == Venda.STATUS_PAGO:
            return format_html(
                '<span style="color: orange;"><b>⚠ Aguardando sincronização</b></span><br>'
                '<small>A venda está marcada como paga mas ainda não tem entrada no financeiro. '
                'Salve novamente para sincronizar.</small>'
            )
        else:
            return format_html('<span style="color: gray;">Não sincronizada (venda não paga)</span>')

    lancamento_financeiro_link.short_description = "Lançamento Financeiro"

    def status_integracao_display(self, obj):
        """Exibe o status de integração."""
        return format_html(
            '<strong>{}</strong>',
            obj.get_status_integracao_display()
        )

    status_integracao_display.short_description = "Status de Integração"

    actions = ["action_sincronizar_agora"]

    def action_sincronizar_agora(self, request, queryset):
        """Ação admin para sincronizar vendas com financeiro manualmente."""
        from vendas.views import _sync_venda_financeiro
        
        sincronizadas = 0
        erros = 0
        
        for venda in queryset:
            try:
                _sync_venda_financeiro(venda)
                sincronizadas += 1
            except Exception as e:
                erros += 1
                self.message_user(request, f"ERRO ao sincronizar venda #{venda.pk}: {str(e)}", level=admin.messages.ERROR)
        
        if sincronizadas:
            self.message_user(
                request,
                f"{sincronizadas} venda(s) sincronizada(s) com sucesso.",
                level=admin.messages.SUCCESS
            )
        if erros:
            self.message_user(
                request,
                f"{erros} erro(s) ao sincronizar. Verifique os detalhes acima.",
                level=admin.messages.ERROR
            )

    action_sincronizar_agora.short_description = "Sincronizar com financeiro agora"
