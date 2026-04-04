from django.db import models

from core.models import TimeStampedModel, AtivoInativoModel, AuditModel


class Linhagem(TimeStampedModel, AtivoInativoModel, AuditModel):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    origem = models.CharField(max_length=100, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Linhagem"
        verbose_name_plural = "Linhagens"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
