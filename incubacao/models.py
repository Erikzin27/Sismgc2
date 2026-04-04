from datetime import timedelta
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel, AuditModel
from aves.models import Ave
from lotes.models import Lote


class Incubacao(TimeStampedModel, AuditModel):
    TIPO_CHOICES = [("chocadeira", "Chocadeira"), ("natural", "Natural")]
    STATUS_EM_ANDAMENTO = "andamento"
    STATUS_CONCLUIDA = "concluida"
    STATUS_CANCELADA = "cancelada"
    STATUS_CHOICES = [
        (STATUS_EM_ANDAMENTO, "Em andamento"),
        (STATUS_CONCLUIDA, "Concluída"),
        (STATUS_CANCELADA, "Cancelada"),
    ]

    codigo = models.CharField(max_length=30, unique=True)
    data_entrada = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade_ovos = models.PositiveIntegerField()
    origem_ovos = models.CharField(max_length=100, blank=True)
    matriz_responsavel = models.ForeignKey(
        Ave, on_delete=models.SET_NULL, null=True, blank=True, related_name="incubacoes_matriz"
    )
    lote_relacionado = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True, related_name="incubacoes")
    previsao_eclosao = models.DateField(blank=True, null=True)
    data_eclosao = models.DateField(blank=True, null=True)
    quantidade_nascida = models.PositiveIntegerField(default=0)
    ovos_fertis = models.PositiveIntegerField(default=0)
    ovos_infertis = models.PositiveIntegerField(default=0)
    perdas = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_EM_ANDAMENTO)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Incubação"
        verbose_name_plural = "Incubações"
        ordering = ["-data_entrada"]

    def save(self, *args, **kwargs):
        if not self.previsao_eclosao and self.data_entrada:
            self.previsao_eclosao = self.data_entrada + timedelta(days=21)
        super().save(*args, **kwargs)

    @property
    def taxa_fertilidade(self):
        if self.quantidade_ovos:
            return (self.ovos_fertis / self.quantidade_ovos) * 100
        return 0

    @property
    def taxa_eclosao(self):
        if self.ovos_fertis:
            return (self.quantidade_nascida / self.ovos_fertis) * 100
        return 0

    @property
    def taxa_perda(self):
        if self.quantidade_ovos:
            return (self.perdas / self.quantidade_ovos) * 100
        return 0

    def __str__(self):
        return self.codigo
