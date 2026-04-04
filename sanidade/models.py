from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel, AuditModel


class Vacina(TimeStampedModel, AuditModel):
    nome = models.CharField(max_length=100)
    fabricante = models.CharField(max_length=100, blank=True)
    dose_recomendada = models.CharField(max_length=50, blank=True)
    carencia_dias = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True)
    receita_anexo = models.FileField(upload_to="sanidade", null=True, blank=True)

    class Meta:
        verbose_name = "Vacina"
        verbose_name_plural = "Vacinas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Medicamento(TimeStampedModel, AuditModel):
    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100, blank=True)
    validade = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class AplicacaoVacina(TimeStampedModel, AuditModel):
    STATUS_PENDENTE = "pendente"
    STATUS_APLICADA = "aplicada"
    STATUS_CANCELADA = "cancelada"
    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_APLICADA, "Aplicada"),
        (STATUS_CANCELADA, "Cancelada"),
    ]

    vacina = models.ForeignKey(Vacina, on_delete=models.CASCADE, related_name="aplicacoes")
    ave = models.ForeignKey("aves.Ave", on_delete=models.SET_NULL, null=True, blank=True, related_name="vacinas")
    lote = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True, related_name="vacinas")
    data_programada = models.DateField()
    data_aplicacao = models.DateField(null=True, blank=True)
    dose = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Aplicação de Vacina"
        verbose_name_plural = "Aplicações de Vacina"
        ordering = ["-data_programada"]

    def __str__(self):
        alvo = self.ave or self.lote
        return f"{self.vacina} - {alvo}"

    @property
    def data_final_carencia(self):
        if self.status != self.STATUS_APLICADA or not self.data_aplicacao or not self.vacina:
            return None
        dias = self.vacina.carencia_dias or 0
        return self.data_aplicacao + timezone.timedelta(days=dias)

    @property
    def carencia_ativa(self):
        fim = self.data_final_carencia
        return bool(fim and fim >= timezone.localdate())


class Tratamento(TimeStampedModel, AuditModel):
    ave = models.ForeignKey("aves.Ave", on_delete=models.SET_NULL, null=True, blank=True, related_name="tratamentos")
    lote = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True, related_name="tratamentos")
    doenca = models.CharField(max_length=100)
    medicamento = models.ForeignKey(Medicamento, on_delete=models.PROTECT, related_name="tratamentos")
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    periodo_carencia = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True)
    receita_anexo = models.FileField(upload_to="sanidade", null=True, blank=True)

    class Meta:
        verbose_name = "Tratamento"
        verbose_name_plural = "Tratamentos"
        ordering = ["-data_inicio"]

    def __str__(self):
        alvo = self.ave or self.lote
        return f"{self.doenca} - {alvo}"

    @property
    def data_final_carencia(self):
        if not self.data_fim:
            return None
        return self.data_fim + timezone.timedelta(days=self.periodo_carencia or 0)

    @property
    def carencia_ativa(self):
        fim = self.data_final_carencia
        return bool(fim and fim >= timezone.localdate())


class VacinaLote(TimeStampedModel, AuditModel):
    lote = models.ForeignKey("lotes.Lote", on_delete=models.CASCADE, related_name="vacinas_lote")
    nome_vacina = models.CharField(max_length=100)
    data_prevista = models.DateField()
    aplicada = models.BooleanField(default=False)
    data_aplicacao = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Vacina do Lote"
        verbose_name_plural = "Vacinas do Lote"
        ordering = ["data_prevista"]
        constraints = [
            models.UniqueConstraint(
                fields=["lote", "nome_vacina", "data_prevista"],
                name="unique_vacina_lote_data",
            )
        ]

    def __str__(self):
        return f"{self.lote} - {self.nome_vacina} ({self.data_prevista})"
