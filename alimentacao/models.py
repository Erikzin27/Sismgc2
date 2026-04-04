from django.db import models
from core.models import TimeStampedModel, AuditModel


class FormulaRacao(TimeStampedModel, AuditModel):
    FASE_CHOICES = [
        ("inicial", "Inicial"),
        ("crescimento", "Crescimento"),
        ("terminacao", "Terminação"),
        ("postura", "Postura"),
        ("reproducao", "Reprodução"),
    ]
    nome = models.CharField(max_length=100)
    fase = models.CharField(max_length=20, choices=FASE_CHOICES)
    ingredientes = models.TextField(help_text="Lista de ingredientes e proporções")
    custo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Fórmula de Ração"
        verbose_name_plural = "Fórmulas de Ração"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
