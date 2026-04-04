from django.db import models

from core.models import TimeStampedModel, AuditModel
from linhagens.models import Linhagem
from lotes.models import Lote


class Nascimento(TimeStampedModel, AuditModel):
    data = models.DateField()
    incubacao = models.ForeignKey("incubacao.Incubacao", on_delete=models.CASCADE, related_name="nascimentos")
    quantidade_nascida = models.PositiveIntegerField()
    quantidade_viva = models.PositiveIntegerField()
    quantidade_morta = models.PositiveIntegerField(default=0)
    linhagem = models.ForeignKey(Linhagem, on_delete=models.PROTECT)
    lote_destino = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="nascimentos")
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Nascimento"
        verbose_name_plural = "Nascimentos"
        ordering = ["-data"]

    def __str__(self):
        return f"Nascimento {self.data} - {self.quantidade_nascida} aves"

    def save(self, *args, **kwargs):
        if self.quantidade_nascida == 0 and (self.quantidade_viva or self.quantidade_morta):
            self.quantidade_nascida = (self.quantidade_viva or 0) + (self.quantidade_morta or 0)
        if (self.quantidade_viva or 0) + (self.quantidade_morta or 0) > (self.quantidade_nascida or 0):
            self.quantidade_nascida = (self.quantidade_viva or 0) + (self.quantidade_morta or 0)
        if self.quantidade_nascida and self.quantidade_viva and self.quantidade_morta == 0:
            diff = self.quantidade_nascida - self.quantidade_viva
            if diff >= 0:
                self.quantidade_morta = diff
        super().save(*args, **kwargs)
