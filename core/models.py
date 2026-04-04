from django.db import models
from django.contrib.auth import get_user_model


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class AtivoInativoModel(models.Model):
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AuditModel(models.Model):
    criado_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_criados",
    )
    atualizado_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_atualizados",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        try:
            from core.threadlocal import get_current_user
        except Exception:
            get_current_user = None
        user = get_current_user() if get_current_user else None
        if user and not self.pk and not self.criado_por_id:
            self.criado_por = user
        if user:
            self.atualizado_por = user
        super().save(*args, **kwargs)


class ConfiguracaoSistema(TimeStampedModel, AuditModel):
    nome_sistema = models.CharField(max_length=100, default="SISMGC")
    nome_granja = models.CharField(max_length=120, blank=True)
    tema_padrao = models.CharField(max_length=10, choices=[("dark", "Escuro"), ("light", "Claro")], default="dark")
    logo_ativa = models.CharField(max_length=200, default="img/logo-mgc.png")
    dias_alerta_vencimento = models.PositiveIntegerField(default=30)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"

    def __str__(self):
        return "Configuração do Sistema"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            from core.services.config import invalidate_configuracao_sistema_cache

            invalidate_configuracao_sistema_cache()
        except Exception:
            pass
