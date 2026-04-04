from django.db import models

from core.models import TimeStampedModel, AtivoInativoModel, AuditModel
from linhagens.models import Linhagem


class Ave(TimeStampedModel, AtivoInativoModel, AuditModel):
    SEXO_MACHO = "M"
    SEXO_FEMEA = "F"
    SEXO_CHOICES = [(SEXO_MACHO, "Macho"), (SEXO_FEMEA, "Fêmea")]

    FINALIDADE_CORTE = "corte"
    FINALIDADE_POSTURA = "postura"
    FINALIDADE_REPRODUCAO = "reproducao"
    FINALIDADE_CHOICES = [
        (FINALIDADE_CORTE, "Corte"),
        (FINALIDADE_POSTURA, "Postura"),
        (FINALIDADE_REPRODUCAO, "Reprodução"),
    ]

    STATUS_VIVA = "viva"
    STATUS_VENDIDA = "vendida"
    STATUS_MORTA = "morta"
    STATUS_ABATIDA = "abatida"
    STATUS_CHOICES = [
        (STATUS_VIVA, "Viva"),
        (STATUS_VENDIDA, "Vendida"),
        (STATUS_MORTA, "Morta"),
        (STATUS_ABATIDA, "Abatida"),
    ]

    codigo_interno = models.CharField(max_length=30, unique=True)
    identificacao = models.CharField("Identificação/Anilha", max_length=50, blank=True)
    nome = models.CharField(max_length=60, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    finalidade = models.CharField(max_length=20, choices=FINALIDADE_CHOICES)
    data_nascimento = models.DateField(null=True, blank=True)
    linhagem = models.ForeignKey(Linhagem, on_delete=models.PROTECT, related_name="aves", null=True, blank=True)
    pai = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="filhos_pai")
    mae = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="filhos_mae")
    origem = models.CharField(max_length=100, blank=True)
    lote_atual = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True, related_name="aves")
    peso_atual = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    valor_referencia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_VIVA)
    observacoes = models.TextField(blank=True)
    foto = models.ImageField(upload_to="aves", null=True, blank=True)

    class Meta:
        verbose_name = "Ave"
        verbose_name_plural = "Aves"
        ordering = ["codigo_interno"]

    def __str__(self):
        return f"{self.codigo_interno} - {self.nome or 'Sem nome'}"
