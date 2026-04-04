from django.contrib import admin
from .models import Vacina, Medicamento, AplicacaoVacina, Tratamento


@admin.register(Vacina)
class VacinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "fabricante", "carencia_dias")
    search_fields = ("nome", "fabricante")


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "validade")
    search_fields = ("nome", "categoria")


@admin.register(AplicacaoVacina)
class AplicacaoVacinaAdmin(admin.ModelAdmin):
    list_display = ("vacina", "ave", "lote", "data_programada", "status")
    list_filter = ("status", "vacina")
    search_fields = ("vacina__nome",)


@admin.register(Tratamento)
class TratamentoAdmin(admin.ModelAdmin):
    list_display = ("doenca", "medicamento", "ave", "lote", "data_inicio", "data_fim")
    list_filter = ("doenca",)
    search_fields = ("doenca", "medicamento__nome")
