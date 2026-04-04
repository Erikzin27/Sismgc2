from django.contrib import admin
from .models import Nascimento
from .forms import NascimentoForm


@admin.register(Nascimento)
class NascimentoAdmin(admin.ModelAdmin):
    form = NascimentoForm
    list_display = ("data", "incubacao", "quantidade_nascida", "lote_destino")
    list_filter = ("data",)
    search_fields = ("incubacao__codigo",)
