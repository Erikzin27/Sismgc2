from django.contrib import admin
from .models import Venda


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ("data", "cliente", "produto", "categoria", "valor_total", "status_pagamento")
    list_filter = ("categoria", "status_pagamento")
    search_fields = ("cliente", "produto")
