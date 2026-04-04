from django.contrib import admin
from core.models import ConfiguracaoSistema


@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ("nome_sistema", "nome_granja", "tema_padrao")
