from django.db import models
from core.models import TimeStampedModel, AuditModel


class Abate(TimeStampedModel, AuditModel):
    data = models.DateField()
    lote = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True, related_name="abates")
    aves = models.ManyToManyField("aves.Ave", blank=True, related_name="abates")
    quantidade_abatida = models.PositiveIntegerField()
    peso_total = models.DecimalField(max_digits=12, decimal_places=2)
    peso_medio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    custo_acumulado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    receita_gerada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    destino = models.CharField(max_length=100, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Abate"
        verbose_name_plural = "Abates"
        ordering = ["-data"]

    def __str__(self):
        return f"Abate {self.data}"

    @property
    def lucro_prejuizo(self):
        return self.receita_gerada - self.custo_acumulado

    def save(self, *args, **kwargs):
        if self.quantidade_abatida and not self.peso_medio:
            self.peso_medio = self.peso_total / self.quantidade_abatida
        super().save(*args, **kwargs)
