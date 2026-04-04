from django.db import models
from decimal import Decimal
from core.models import TimeStampedModel, AuditModel


class Venda(TimeStampedModel, AuditModel):
    CAT_OVOS = "ovos"
    CAT_AVE_VIVA = "ave_viva"
    CAT_AVE_ABATIDA = "ave_abatida"
    CAT_REPRODUTOR = "reprodutor"
    CAT_MATRIZ = "matriz"
    CAT_OUTROS = "outros"
    CATEGORIAS = [
        (CAT_OVOS, "Ovos"),
        (CAT_AVE_VIVA, "Ave viva"),
        (CAT_AVE_ABATIDA, "Ave abatida"),
        (CAT_REPRODUTOR, "Reprodutor"),
        (CAT_MATRIZ, "Matriz"),
        (CAT_OUTROS, "Outros"),
    ]

    STATUS_PAGO = "pago"
    STATUS_PENDENTE = "pendente"
    STATUS_CANCELADO = "cancelado"
    STATUS_CHOICES = [
        (STATUS_PAGO, "Pago"),
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_CANCELADO, "Cancelado"),
    ]

    data = models.DateField()
    cliente = models.CharField(max_length=100)
    produto = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)
    unidade = models.CharField(max_length=20, default="un")
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    forma_pagamento = models.CharField(max_length=50, blank=True)
    status_pagamento = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    observacoes = models.TextField(blank=True)
    lote = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True, related_name="vendas")
    ave = models.ForeignKey("aves.Ave", on_delete=models.SET_NULL, null=True, blank=True, related_name="vendas")

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-data"]
        indexes = [
            models.Index(fields=["status_pagamento", "data"], name="vendas_vend_status__cf9f81_idx"),
            models.Index(fields=["lote", "data"], name="vendas_vend_lote_id_6107c7_idx"),
            models.Index(fields=["categoria", "data"], name="vendas_vend_categor_65684d_idx"),
        ]

    def __str__(self):
        return f"Venda {self.data} - {self.cliente}"

    def save(self, *args, **kwargs):
        if self.valor_total is None or self.valor_total == 0:
            self.valor_total = ((self.quantidade or 0) * (self.valor_unitario or 0) - (self.desconto or 0)).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
