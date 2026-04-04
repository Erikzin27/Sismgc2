from django.db import models
from django.contrib.auth import get_user_model

from core.models import TimeStampedModel


class HistoricoEvento(TimeStampedModel):
    ACAO_CHOICES = [
        ("create", "Criação"),
        ("update", "Atualização"),
        ("delete", "Exclusão"),
        ("status", "Status"),
    ]

    entidade = models.CharField(max_length=50)
    referencia_id = models.PositiveIntegerField()
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES, default="update")
    descricao = models.TextField()
    detalhes = models.JSONField(default=dict, blank=True)
    usuario = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Histórico"
        verbose_name_plural = "Históricos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entidade", "referencia_id", "created_at"], name="historico_h_entidad_1995bc_idx"),
            models.Index(fields=["entidade", "acao", "created_at"], name="historico_h_entidad_b31347_idx"),
            models.Index(fields=["usuario", "created_at"], name="historico_h_usuario_69b459_idx"),
        ]

    def __str__(self):
        return f"{self.entidade} #{self.referencia_id} - {self.descricao[:30]}"
