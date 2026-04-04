from django.db import models
from core.models import TimeStampedModel, AuditModel


class LancamentoFinanceiro(TimeStampedModel, AuditModel):
    TIPO_ENTRADA = "entrada"
    TIPO_SAIDA = "saida"
    TIPOS = [(TIPO_ENTRADA, "Entrada"), (TIPO_SAIDA, "Saída")]

    CAT_RACAO = "racao"
    CAT_VACINA = "vacinas"
    CAT_MEDICAMENTO = "medicamentos"
    CAT_ENERGIA = "energia"
    CAT_TRANSPORTE = "transporte"
    CAT_MANUTENCAO = "manutencao"
    CAT_MAO_OBRA = "mao_obra"
    CAT_EQUIP = "equipamentos"
    CAT_VENDA = "vendas"
    CAT_OUTROS = "outros"
    CATEGORIAS = [
        (CAT_RACAO, "Ração"),
        (CAT_VACINA, "Vacinas"),
        (CAT_MEDICAMENTO, "Medicamentos"),
        (CAT_ENERGIA, "Energia"),
        (CAT_TRANSPORTE, "Transporte"),
        (CAT_MANUTENCAO, "Manutenção"),
        (CAT_MAO_OBRA, "Mão de obra"),
        (CAT_EQUIP, "Equipamentos"),
        (CAT_VENDA, "Venda"),
        (CAT_OUTROS, "Outros"),
    ]

    data = models.DateField()
    tipo = models.CharField(max_length=10, choices=TIPOS)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    descricao = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    lote = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True, related_name="lancamentos")
    ave = models.ForeignKey("aves.Ave", on_delete=models.SET_NULL, null=True, blank=True, related_name="lancamentos")
    forma_pagamento = models.CharField(max_length=50, blank=True)
    observacoes = models.TextField(blank=True)
    comprovante = models.FileField(upload_to="financeiro", null=True, blank=True)
    venda = models.OneToOneField("vendas.Venda", on_delete=models.SET_NULL, null=True, blank=True, related_name="lancamento_financeiro")

    class Meta:
        verbose_name = "Lançamento Financeiro"
        verbose_name_plural = "Lançamentos Financeiros"
        ordering = ["-data"]
        indexes = [
            models.Index(fields=["tipo", "data"], name="financeiro__tipo_244d6d_idx"),
            models.Index(fields=["categoria", "data"], name="financeiro__categor_3c8dbf_idx"),
            models.Index(fields=["lote", "data"], name="financeiro__lote_id_4909cf_idx"),
            models.Index(fields=["venda"], name="financeiro__venda_i_340fc8_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao} ({self.valor})"


class OrcamentoFuturo(TimeStampedModel, AuditModel):
    STATUS_PLANEJADO = "planejado"
    STATUS_ANDAMENTO = "andamento"
    STATUS_CONCLUIDO = "concluido"
    STATUS_CANCELADO = "cancelado"
    STATUS_CHOICES = [
        (STATUS_PLANEJADO, "Planejado"),
        (STATUS_ANDAMENTO, "Em andamento"),
        (STATUS_CONCLUIDO, "Concluído"),
        (STATUS_CANCELADO, "Cancelado"),
    ]

    PRIORIDADE_BAIXA = "baixa"
    PRIORIDADE_MEDIA = "media"
    PRIORIDADE_ALTA = "alta"
    PRIORIDADE_CHOICES = [
        (PRIORIDADE_BAIXA, "Baixa"),
        (PRIORIDADE_MEDIA, "Média"),
        (PRIORIDADE_ALTA, "Alta"),
    ]

    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    valor_previsto = models.DecimalField(max_digits=12, decimal_places=2)
    valor_ja_reservado = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANEJADO)
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default=PRIORIDADE_MEDIA)
    data_planejada = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    foto = models.ImageField(upload_to="orcamentos", null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Orçamento Futuro"
        verbose_name_plural = "Orçamentos Futuros"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "prioridade", "ativo"], name="financeiro__status_0764c1_idx"),
            models.Index(fields=["data_planejada"], name="financeiro__data_pl_af728f_idx"),
        ]

    def __str__(self):
        return self.titulo

    @property
    def valor_disponivel_planejado(self):
        return self.valor_ja_reservado or 0

    @property
    def falta_interna(self):
        faltante = (self.valor_previsto or 0) - (self.valor_ja_reservado or 0)
        return faltante if faltante > 0 else 0
