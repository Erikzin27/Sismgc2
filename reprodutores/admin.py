from django.contrib import admin
from django.utils.html import format_html
from .models import Reprodutor, Casal


def _tipo_badge(obj):
    if obj.tipo == Reprodutor.TIPO_MATRIZ:
        return format_html('<span class="badge bg-danger">♀ Matriz</span>')
    else:
        return format_html('<span class="badge bg-primary">♂ Reprodutor</span>')

_tipo_badge.short_description = "Tipo"


def _status_badge(obj):
    status_colors = {
        Reprodutor.STATUS_ATIVO: "success",
        Reprodutor.STATUS_DESCANSO: "warning",
        Reprodutor.STATUS_VENDIDO: "info",
        Reprodutor.STATUS_DESCARTADO: "danger",
    }
    color = status_colors.get(obj.status, "secondary")
    return format_html(f'<span class="badge bg-{color}">{obj.get_status_display()}</span>')

_status_badge.short_description = "Status"


def _qualidade_badge(obj):
    qualidade_colors = {
        Reprodutor.QUALIDADE_PADRAO: "secondary",
        Reprodutor.QUALIDADE_SUPERIOR: "info",
        Reprodutor.QUALIDADE_PURA: "success",
    }
    color = qualidade_colors.get(obj.qualidade_genetica, "secondary")
    return format_html(f'<span class="badge bg-{color}">{obj.get_qualidade_genetica_display()}</span>')

_qualidade_badge.short_description = "Qualidade"


@admin.register(Reprodutor)
class ReprodutorAdmin(admin.ModelAdmin):
    list_display = (
        "ave",
        _tipo_badge,
        _status_badge,
        _qualidade_badge,
        "valor_estimado",
        "data_inicio_reproducao",
        "ativo",
    )
    list_filter = ("tipo", "status", "qualidade_genetica", "ativo", "data_inicio_reproducao")
    search_fields = ("ave__codigo_interno", "ave__nome")
    readonly_fields = ("created_at", "updated_at", "ave_link")
    
    fieldsets = (
        ("Ave Relacionada", {
            "fields": ("ave", "ave_link"),
        }),
        ("Classificação e Status", {
            "fields": ("tipo", "status", "qualidade_genetica", "ativo"),
        }),
        ("Informações Financeiras", {
            "fields": ("valor_estimado",),
        }),
        ("Datas", {
            "fields": ("data_inicio_reproducao", "data_fim_reproducao"),
        }),
        ("Observações", {
            "fields": ("observacoes",),
        }),
        ("Auditoria", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def ave_link(self, obj):
        """Link para a ave no admin."""
        if obj.ave:
            from django.urls import reverse
            url = reverse('admin:aves_ave_change', args=[obj.ave.pk])
            return format_html(
                '<a href="{}" target="_blank">Ver ave #{} - {}</a>',
                url,
                obj.ave.pk,
                obj.ave.codigo_interno
            )
        return "-"

    ave_link.short_description = "Detalhes da Ave"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("ave",)
        return self.readonly_fields


@admin.register(Casal)
class CasalAdmin(admin.ModelAdmin):
    list_display = (
        "reprodutor_macho_info",
        "matriz_femea_info",
        "status_badge",
        "data_inicio",
        "duracao",
        "ativo",
    )
    list_filter = ("status", "ativo", "data_inicio")
    search_fields = (
        "reprodutor_macho__ave__codigo_interno",
        "matriz_femea__ave__codigo_interno",
    )
    readonly_fields = ("created_at", "updated_at", "duracao_display")
    
    fieldsets = (
        ("Casal", {
            "fields": ("reprodutor_macho", "matriz_femea"),
        }),
        ("Informações", {
            "fields": ("lote", "status", "data_inicio", "data_fim"),
        }),
        ("Desempenho", {
            "fields": ("duracao_display",),
        }),
        ("Observações", {
            "fields": ("observacoes",),
        }),
        ("Auditoria", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def reprodutor_macho_info(self, obj):
        if obj.reprodutor_macho:
            return format_html(
                '♂ {} - {}',
                obj.reprodutor_macho.ave.codigo_interno,
                obj.reprodutor_macho.ave.nome or "Sem nome"
            )
        return "-"

    reprodutor_macho_info.short_description = "Macho"

    def matriz_femea_info(self, obj):
        if obj.matriz_femea:
            return format_html(
                '♀ {} - {}',
                obj.matriz_femea.ave.codigo_interno,
                obj.matriz_femea.ave.nome or "Sem nome"
            )
        return "-"

    matriz_femea_info.short_description = "Fêmea"

    def status_badge(self, obj):
        colors = {
            Casal.STATUS_PLANEJADO: "warning",
            Casal.STATUS_ATIVO: "success",
            Casal.STATUS_PAUSADO: "info",
            Casal.STATUS_CONCLUIDO: "secondary",
        }
        color = colors.get(obj.status, "secondary")
        return format_html(f'<span class="badge bg-{color}">{obj.get_status_display()}</span>')

    status_badge.short_description = "Status"

    def duracao(self, obj):
        return format_html(f'{obj.duracao_reproducao} dias')

    duracao.short_description = "Duração"

    def duracao_display(self, obj):
        return f"{obj.duracao_reproducao} dias de atividade reprodutiva"

    duracao_display.short_description = "Duração da Reprodução"
