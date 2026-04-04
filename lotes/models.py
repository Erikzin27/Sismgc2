from django.db import models

from core.models import TimeStampedModel, AtivoInativoModel, AuditModel
from linhagens.models import Linhagem


class Lote(TimeStampedModel, AtivoInativoModel, AuditModel):
    FINALIDADE_CHOICES = [
        ("corte", "Corte"),
        ("postura", "Postura"),
        ("reproducao", "Reprodução"),
    ]
    STATUS_ATIVO = "ativo"
    STATUS_ENCERRADO = "encerrado"
    STATUS_CHOICES = [(STATUS_ATIVO, "Ativo"), (STATUS_ENCERRADO, "Encerrado")]
    REPRO_STATUS_ATIVO = "ativo"
    REPRO_STATUS_PAUSADO = "pausado"
    REPRO_STATUS_ENCERRADO = "encerrado"
    REPRO_STATUS_CHOICES = [
        (REPRO_STATUS_ATIVO, "Ativo"),
        (REPRO_STATUS_PAUSADO, "Pausado"),
        (REPRO_STATUS_ENCERRADO, "Encerrado"),
    ]

    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=30, unique=True)
    data_criacao = models.DateField()
    finalidade = models.CharField(max_length=20, choices=FINALIDADE_CHOICES)
    linhagem_principal = models.ForeignKey(Linhagem, on_delete=models.PROTECT, related_name="lotes", null=True, blank=True)
    quantidade_inicial = models.PositiveIntegerField()
    quantidade_atual = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ATIVO)
    local = models.CharField(max_length=100, blank=True)
    observacoes = models.TextField(blank=True)
    custo_acumulado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consumo_acumulado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reprodutivo = models.BooleanField(default=False)
    quantidade_machos = models.PositiveIntegerField(default=0)
    quantidade_femeas = models.PositiveIntegerField(default=0)
    data_inicio_reproducao = models.DateField(null=True, blank=True)
    status_reprodutivo = models.CharField(
        max_length=20,
        choices=REPRO_STATUS_CHOICES,
        blank=True,
    )
    observacoes_reproducao = models.TextField(blank=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"{self.nome} ({self.codigo})"

    def save(self, *args, **kwargs):
        if self.quantidade_atual is None:
            self.quantidade_atual = self.quantidade_inicial
        if self.finalidade == "reproducao" and not self.reprodutivo:
            self.reprodutivo = True
        if not self.reprodutivo:
            self.quantidade_machos = 0
            self.quantidade_femeas = 0
            self.data_inicio_reproducao = None
            self.status_reprodutivo = ""
            self.observacoes_reproducao = ""
        super().save(*args, **kwargs)

    @property
    def custo_por_ave(self):
        if self.quantidade_atual:
            return self.custo_acumulado / self.quantidade_atual
        return 0

    @property
    def custo_racao(self):
        from estoque.models import MovimentoEstoque, ItemEstoque
        return (
            MovimentoEstoque.objects.filter(lote_relacionado=self, item__categoria=ItemEstoque.CAT_RACAO)
            .aggregate(total=models.Sum("custo_unitario"))["total"]
            or 0
        )

    @property
    def despesas_extras(self):
        from financeiro.models import LancamentoFinanceiro
        return (
            LancamentoFinanceiro.objects.filter(lote=self, tipo=LancamentoFinanceiro.TIPO_SAIDA).aggregate(
                total=models.Sum("valor")
            )["total"]
            or 0
        )

    @property
    def receita_vendas(self):
        from vendas.models import Venda
        return (
            Venda.objects.filter(lote=self).aggregate(total=models.Sum("valor_total"))["total"]
            or 0
        )

    @property
    def custo_sanitario(self):
        from financeiro.models import LancamentoFinanceiro

        return (
            LancamentoFinanceiro.objects.filter(
                lote=self,
                tipo=LancamentoFinanceiro.TIPO_SAIDA,
                categoria__in=[
                    LancamentoFinanceiro.CAT_VACINA,
                    LancamentoFinanceiro.CAT_MEDICAMENTO,
                ],
            ).aggregate(total=models.Sum("valor"))["total"]
            or 0
        )

    @property
    def lucro_final(self):
        return self.receita_vendas - (self.custo_racao + self.despesas_extras)

    @property
    def mortalidade_percentual(self):
        if not self.quantidade_inicial:
            return 0
        mortos = max(self.quantidade_inicial - (self.quantidade_atual or 0), 0)
        return (mortos / self.quantidade_inicial) * 100

    @property
    def consumo_racao_total(self):
        from estoque.models import MovimentoEstoque, ItemEstoque
        return (
            MovimentoEstoque.objects.filter(lote_relacionado=self, item__categoria=ItemEstoque.CAT_RACAO)
            .aggregate(total=models.Sum("quantidade"))["total"]
            or 0
        )

    @property
    def conversao_alimentar(self):
        if self.quantidade_inicial and self.consumo_racao_total:
            return self.consumo_racao_total / self.quantidade_inicial
        return 0

    @property
    def proporcao_reprodutiva(self):
        if not self.reprodutivo or not self.quantidade_femeas:
            return "-"
        return f"1:{round(self.quantidade_femeas / max(self.quantidade_machos, 1), 1)}"

    @property
    def proporcao_reprodutiva_valor(self):
        if not self.reprodutivo or not self.quantidade_femeas or not self.quantidade_machos:
            return 0
        return self.quantidade_femeas / self.quantidade_machos

    @property
    def resumo_incubacao(self):
        incubacoes = self.incubacoes.all()
        nascimentos = self.nascimentos.all()
        total_incubacoes = incubacoes.count()
        total_ovos = incubacoes.aggregate(total=models.Sum("quantidade_ovos"))["total"] or 0
        total_nascidos = nascimentos.aggregate(total=models.Sum("quantidade_nascida"))["total"] or 0
        taxa_eclosao = 0
        if total_ovos:
            taxa_eclosao = (total_nascidos / total_ovos) * 100
        return {
            "total_incubacoes": total_incubacoes,
            "total_ovos": total_ovos,
            "total_nascidos": total_nascidos,
            "taxa_eclosao": taxa_eclosao,
        }
