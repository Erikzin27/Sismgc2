from django.db import models
from core.models import TimeStampedModel, AuditModel
from aves.models import Ave


class RegistroGenetico(TimeStampedModel, AuditModel):
    pai = models.ForeignKey(Ave, on_delete=models.SET_NULL, null=True, related_name="registros_como_pai")
    mae = models.ForeignKey(Ave, on_delete=models.SET_NULL, null=True, related_name="registros_como_mae")
    filho = models.ForeignKey(Ave, on_delete=models.CASCADE, related_name="registro_genetico")
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Registro Genético"
        verbose_name_plural = "Registros Genéticos"
        unique_together = ("pai", "mae", "filho")

    def __str__(self):
        return f"{self.filho} - Pais: {self.pai} / {self.mae}"
