from django.contrib import admin
from .models import Incubacao


@admin.register(Incubacao)
class IncubacaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "data_entrada", "tipo", "quantidade_ovos", "previsao_eclosao", "status")
    list_filter = ("tipo", "status")
    search_fields = ("codigo", "origem_ovos")
