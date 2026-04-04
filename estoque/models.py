from django.db import models
from core.models import TimeStampedModel, AuditModel


class ItemEstoque(TimeStampedModel, AuditModel):
    CAT_RACAO = "racao"
    CAT_GRAOS = "graos"
    CAT_VACINA = "vacina"
    CAT_MEDICAMENTO = "medicamento"
    CAT_MATERIAL = "material"
    CAT_OUTROS = "outros"
    CATEGORIAS = [
        (CAT_RACAO, "Ração"),
        (CAT_GRAOS, "Grãos/Ingredientes"),
        (CAT_VACINA, "Vacina"),
        (CAT_MEDICAMENTO, "Medicamento"),
        (CAT_MATERIAL, "Material"),
        (CAT_OUTROS, "Outros"),
    ]

    UN_KG = "kg"
    UN_G = "g"
    UN_UN = "un"
    UN_ML = "ml"
    UN_L = "l"
    UN_OVOS = "ovos"
    UNIDADES = [
        (UN_KG, "kg"),
        (UN_G, "g"),
        (UN_UN, "un"),
        (UN_ML, "ml"),
        (UN_L, "L"),
        (UN_OVOS, "ovos"),
    ]

    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    unidade = models.CharField(max_length=20, choices=UNIDADES, default=UN_UN)
    quantidade_atual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estoque_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    custo_medio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultimo_preco = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    validade = models.DateField(null=True, blank=True)
    fornecedor = models.CharField(max_length=100, blank=True)
    localizacao = models.CharField(max_length=100, blank=True)
    observacoes = models.TextField(blank=True)
    anexo = models.FileField(upload_to="estoque", null=True, blank=True)

    class Meta:
        verbose_name = "Item de Estoque"
        verbose_name_plural = "Itens de Estoque"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["categoria", "nome"], name="estoque_ite_categor_3c8216_idx"),
            models.Index(fields=["validade"], name="estoque_ite_validad_59a218_idx"),
        ]

    def __str__(self):
        return self.nome

    @property
    def estoque_baixo(self):
        return self.quantidade_atual is not None and self.quantidade_atual <= (self.estoque_minimo or 0)

    @property
    def vencido(self):
        if not self.validade:
            return False
        from django.utils import timezone

        return self.validade < timezone.now().date()

    @property
    def vencendo(self):
        if not self.validade:
            return False
        from django.utils import timezone
        from datetime import timedelta

        hoje = timezone.now().date()
        return hoje <= self.validade <= (hoje + timedelta(days=30))


class MovimentoEstoque(TimeStampedModel, AuditModel):
    TIPO_ENTRADA = "entrada"
    TIPO_SAIDA = "saida"
    TIPO_AJUSTE = "ajuste"
    TIPOS = [(TIPO_ENTRADA, "Entrada"), (TIPO_SAIDA, "Saída"), (TIPO_AJUSTE, "Ajuste")]
    MOTIVO_COMPRA = "compra"
    MOTIVO_CONSUMO = "consumo"
    MOTIVO_DESCARTE = "descarte"
    MOTIVO_AJUSTE = "ajuste"
    MOTIVO_SANITARIO = "uso_sanitario"
    MOTIVO_LOTE = "uso_lote"
    MOTIVOS = [
        (MOTIVO_COMPRA, "Compra"),
        (MOTIVO_CONSUMO, "Consumo"),
        (MOTIVO_DESCARTE, "Descarte/Perda"),
        (MOTIVO_AJUSTE, "Ajuste"),
        (MOTIVO_SANITARIO, "Uso sanitário"),
        (MOTIVO_LOTE, "Uso em lote"),
    ]

    item = models.ForeignKey(ItemEstoque, on_delete=models.CASCADE, related_name="movimentacoes")
    data = models.DateField()
    tipo = models.CharField(max_length=10, choices=TIPOS)
    motivo = models.CharField(max_length=20, choices=MOTIVOS, default=MOTIVO_COMPRA)
    quantidade = models.DecimalField(max_digits=12, decimal_places=2)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lote_relacionado = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True)
    fornecedor = models.CharField(max_length=100, blank=True)
    observacoes = models.TextField(blank=True)
    anexo = models.FileField(upload_to="estoque", null=True, blank=True)

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ["-data", "-created_at"]
        indexes = [
            models.Index(fields=["item", "data"], name="estoque_mov_item_id_f51f97_idx"),
            models.Index(fields=["tipo", "data"], name="estoque_mov_tipo_215782_idx"),
            models.Index(fields=["lote_relacionado", "data"], name="estoque_mov_lote_re_1fcdec_idx"),
            models.Index(fields=["motivo", "data"], name="estoque_mov_motivo_622af0_idx"),
        ]

    def __str__(self):
        return f"{self.tipo} {self.quantidade} {self.item}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        item = self.item
        if creating and item:
            qtd_atual = item.quantidade_atual or 0
            if self.tipo == self.TIPO_ENTRADA:
                novo_qtd = qtd_atual + (self.quantidade or 0)
                if self.custo_unitario:
                    item.ultimo_preco = self.custo_unitario
                    total_custo = (item.custo_medio or 0) * qtd_atual + (self.custo_unitario * (self.quantidade or 0))
                    if novo_qtd:
                        item.custo_medio = total_custo / novo_qtd
                item.quantidade_atual = novo_qtd
            elif self.tipo == self.TIPO_SAIDA:
                item.quantidade_atual = qtd_atual - (self.quantidade or 0)
            elif self.tipo == self.TIPO_AJUSTE:
                item.quantidade_atual = self.quantidade or 0
        super().save(*args, **kwargs)
        if creating and item:
            item.save()
