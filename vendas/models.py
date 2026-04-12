from django.db import models
from decimal import Decimal
from core.models import TimeStampedModel, AuditModel
from core.state_machines import VendaPaymentStateMachine


class Venda(VendaPaymentStateMachine, TimeStampedModel, AuditModel):
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
            from decimal import Decimal
            qty = Decimal(str(self.quantidade or 0))
            unit_val = Decimal(str(self.valor_unitario or 0))
            disc = Decimal(str(self.desconto or 0))
            self.valor_total = (qty * unit_val - disc).quantize(Decimal("0.01"))
        # Validar estados antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def tem_entrada_financeira(self):
        """
        Verifica se a venda tem entrada no financeiro vinculada.
        Útil para templates e verificações.
        """
        return hasattr(self, 'lancamento_financeiro') and self.lancamento_financeiro is not None

    @property
    def status_integracao(self):
        """
        Retorna o status da integração com financeiro.
        - 'vinculada': venda paga com entrada financeira
        - 'pendente_vínculo': venda paga mas sem entrada (erro)
        - 'não_sincronizada': venda não paga
        """
        if self.status_pagamento == self.STATUS_PAGO:
            if self.tem_entrada_financeira:
                return 'vinculada'
            else:
                return 'pendente_vínculo'
        else:
            return 'não_sincronizada'

    def get_status_integracao_display(self):
        """Retorna label legível do status de integração."""
        status_map = {
            'vinculada': 'Entrada gerada ✓',
            'pendente_vínculo': '⚠ Aguardando vínculo',
            'não_sincronizada': 'Sem entrada (normal)',
        }
        return status_map.get(self.status_integracao, 'Desconhecido')

    @property
    def saldo_financeiro(self):
        """
        Retorna o valor do lançamento financeiro vinculado, ou None se não há.
        Útil para relatórios e dashboards.
        """
        if self.tem_entrada_financeira:
            return self.lancamento_financeiro.valor
        return None

    def clean(self):
        """
        Validações adicionais para evitar estados inválidos.
        Útil para garantir integridade de dados.
        """
        # Validar transições de estado primeiro (StateTransitionMixin)
        super().clean()
        
        from django.core.exceptions import ValidationError
        
        # Validar que quantidade e valor_unitario são positivos
        if self.quantidade and self.quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero')
        if self.valor_unitario and self.valor_unitario < 0:
            raise ValidationError('Valor unitário não pode ser negativo')
        if self.desconto and self.desconto < 0:
            raise ValidationError('Desconto não pode ser negativo')
