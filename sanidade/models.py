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

    @property
    def atrasada(self):
        hoje = timezone.localdate()
        return bool(self.status == self.STATUS_PENDENTE and self.data_programada and self.data_programada < hoje)

    @property
    def prevista_hoje(self):
        return bool(
            self.status == self.STATUS_PENDENTE
            and self.data_programada
            and self.data_programada == timezone.localdate()
        )

    @property
    def proxima(self):
        hoje = timezone.localdate()
        return bool(
            self.status == self.STATUS_PENDENTE
            and self.data_programada
            and hoje < self.data_programada <= hoje + timezone.timedelta(days=7)
        )

    @property
    def status_operacional(self):
        if self.status == self.STATUS_APLICADA:
            return "aplicada"
        if self.status == self.STATUS_CANCELADA:
            return "cancelada"
        if self.atrasada:
            return "atrasada"
        if self.prevista_hoje:
            return "hoje"
        if self.proxima:
            return "proxima"
        return "pendente"

    @property
    def status_operacional_label(self):
        labels = {
            "aplicada": "Aplicada / OK",
            "cancelada": "Cancelada",
            "atrasada": "Atrasada",
            "hoje": "Prevista para hoje",
            "proxima": "Próxima",
            "pendente": "Pendente",
        }
        return labels.get(self.status_operacional, self.get_status_display())

    @property
    def dias_atraso(self):
        if not self.atrasada:
            return 0
        return (timezone.localdate() - self.data_programada).days

    @property
    def urgencia_operacional(self):
        if not self.atrasada:
            return ""
        if self.dias_atraso >= 7:
            return "critica"
        if self.dias_atraso >= 3:
            return "alta"
        return "moderada"


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

    @property
    def em_andamento(self):
        hoje = timezone.localdate()
        if self.data_fim and self.data_fim < hoje:
            return False
        return self.data_inicio <= hoje


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

    @property
    def atrasada(self):
        return bool(not self.aplicada and self.data_prevista and self.data_prevista < timezone.localdate())

    @property
    def prevista_hoje(self):
        return bool(not self.aplicada and self.data_prevista == timezone.localdate())

    @property
    def proxima(self):
        hoje = timezone.localdate()
        return bool(not self.aplicada and self.data_prevista and hoje < self.data_prevista <= hoje + timezone.timedelta(days=7))

    @property
    def status_operacional(self):
        if self.aplicada:
            return "aplicada"
        if self.atrasada:
            return "atrasada"
        if self.prevista_hoje:
            return "hoje"
        if self.proxima:
            return "proxima"
        return "pendente"

    @property
    def status_operacional_label(self):
        labels = {
            "aplicada": "Aplicada / OK",
            "atrasada": "Atrasada",
            "hoje": "Prevista para hoje",
            "proxima": "Próxima",
            "pendente": "Pendente",
        }
        return labels.get(self.status_operacional, "Pendente")

    @property
    def observacao_operacional(self):
        if self.aplicada and self.data_aplicacao:
            return f"Aplicada em {self.data_aplicacao}"
        if self.atrasada:
            return f"Aplicação em atraso há {self.dias_atraso} dia(s)."
        if self.prevista_hoje:
            return "Aplicação prevista para hoje."
        if self.proxima:
            return "Aplicação próxima dentro da janela de 7 dias."
        return "Aguardando a data prevista."

    @property
    def dias_atraso(self):
        if not self.atrasada:
            return 0
        return (timezone.localdate() - self.data_prevista).days

    @property
    def urgencia_operacional(self):
        if not self.atrasada:
            return ""
        if self.dias_atraso >= 7:
            return "critica"
        if self.dias_atraso >= 3:
            return "alta"
        return "moderada"
