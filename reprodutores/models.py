from django.db import models
from decimal import Decimal
from core.models import TimeStampedModel, AtivoInativoModel, AuditModel
from aves.models import Ave


class Reprodutor(TimeStampedModel, AtivoInativoModel, AuditModel):
    """
    Registro de aves usadas para reprodução.
    Cada reprodutor é vinculado a uma Ave existente.
    """
    
    TIPO_MATRIZ = "matriz"
    TIPO_REPRODUTOR = "reprodutor"
    TIPOS = [
        (TIPO_MATRIZ, "Matriz (Fêmea)"),
        (TIPO_REPRODUTOR, "Reprodutor (Macho)"),
    ]

    STATUS_ATIVO = "ativo"
    STATUS_DESCANSO = "descanso"
    STATUS_VENDIDO = "vendido"
    STATUS_DESCARTADO = "descartado"
    STATUS_CHOICES = [
        (STATUS_ATIVO, "Ativo"),
        (STATUS_DESCANSO, "Em descanso"),
        (STATUS_VENDIDO, "Vendido"),
        (STATUS_DESCARTADO, "Descartado"),
    ]

    QUALIDADE_PADRAO = "padrao"
    QUALIDADE_SUPERIOR = "superior"
    QUALIDADE_PURA = "pura"
    QUALIDADE_CHOICES = [
        (QUALIDADE_PADRAO, "Padrão"),
        (QUALIDADE_SUPERIOR, "Superior"),
        (QUALIDADE_PURA, "Pura/Linha"),
    ]

    # Relacionamentos
    ave = models.OneToOneField(Ave, on_delete=models.CASCADE, related_name="reprodutor", 
                               help_text="Ave que será usada para reprodução")
    
    # Classificação
    tipo = models.CharField(max_length=20, choices=TIPOS, help_text="Matriz (fêmea) ou Reprodutor (macho)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ATIVO)
    qualidade_genetica = models.CharField(max_length=20, choices=QUALIDADE_CHOICES, default=QUALIDADE_PADRAO)

    # Informações de valor
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                        help_text="Valor estimado para venda ou seguro")
    
    # Datas
    data_inicio_reproducao = models.DateField(null=True, blank=True, 
                                             help_text="Data em que começou a participar de reproduções")
    data_fim_reproducao = models.DateField(null=True, blank=True, 
                                          help_text="Data em que foi retirado da reprodução (se aplicável)")

    # Observações
    observacoes = models.TextField(blank=True, help_text="Notas sobre performance genética, problemas, etc")

    class Meta:
        verbose_name = "Reprodutor"
        verbose_name_plural = "Reprodutores"
        ordering = ["tipo", "-data_inicio_reproducao"]
        indexes = [
            models.Index(fields=["tipo", "ativo"], name="repr_tipo_ativo_idx"),
            models.Index(fields=["status"], name="repr_status_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.ave.codigo_interno} ({self.ave.nome or 'Sem nome'})"

    def save(self, *args, **kwargs):
        # Validação: Tipo deve corresponder ao sexo da ave
        if self.tipo == self.TIPO_MATRIZ and self.ave.sexo != Ave.SEXO_FEMEA:
            raise ValueError("Uma matriz deve ser uma ave fêmea")
        if self.tipo == self.TIPO_REPRODUTOR and self.ave.sexo != Ave.SEXO_MACHO:
            raise ValueError("Um reprodutor deve ser uma ave macho")
        
        # Força a ave ter finalidade reprodução
        if self.ave.finalidade != Ave.FINALIDADE_REPRODUCAO:
            self.ave.finalidade = Ave.FINALIDADE_REPRODUCAO
            self.ave.save()
        
        super().save(*args, **kwargs)

    @property
    def disponivel_para_casal(self):
        """Verifica se o reprodutor está disponível para formar casal."""
        return (self.ativo and 
                self.status == self.STATUS_ATIVO and 
                self.ave.status == Ave.STATUS_VIVA)

    def get_casais_ativos(self):
        """Retorna casais em que este reprodutor está participando."""
        if self.tipo == self.TIPO_MATRIZ:
            return self.casais_como_femea.filter(ativo=True)
        else:
            return self.casais_como_macho.filter(ativo=True)


class Casal(TimeStampedModel, AtivoInativoModel, AuditModel):
    """
    Registro de casais reprodutores.
    Agrupa uma matriz (fêmea) com um reprodutor (macho).
    """

    STATUS_PLANEJADO = "planejado"
    STATUS_ATIVO = "ativo"
    STATUS_PAUSADO = "pausado"
    STATUS_CONCLUIDO = "concluido"
    STATUS_CHOICES = [
        (STATUS_PLANEJADO, "Planejado"),
        (STATUS_ATIVO, "Ativo"),
        (STATUS_PAUSADO, "Pausado"),
        (STATUS_CONCLUIDO, "Concluído"),
    ]

    # Relacionamentos
    reprodutor_macho = models.ForeignKey(Reprodutor, on_delete=models.SET_NULL, null=True, 
                                         related_name="casais_como_macho",
                                         limit_choices_to={'tipo': Reprodutor.TIPO_REPRODUTOR},
                                         help_text="Reprodutor macho")
    
    matriz_femea = models.ForeignKey(Reprodutor, on_delete=models.SET_NULL, null=True, 
                                     related_name="casais_como_femea",
                                     limit_choices_to={'tipo': Reprodutor.TIPO_MATRIZ},
                                     help_text="Matriz fêmea")

    # Informações do casal
    data_inicio = models.DateField(help_text="Data em que o casal começou a reproduzir")
    data_fim = models.DateField(null=True, blank=True, help_text="Data em que o casal foi separado")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANEJADO)
    
    # Observações
    observacoes = models.TextField(blank=True, help_text="Notas sobre o desempenho do casal")
    lote = models.ForeignKey("lotes.Lote", on_delete=models.SET_NULL, null=True, blank=True,
                            help_text="Lote onde o casal está alojado")

    class Meta:
        verbose_name = "Casal Reprodutor"
        verbose_name_plural = "Casais Reprodutores"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["status", "ativo"], name="casal_status_ativo_idx"),
            models.Index(fields=["data_inicio"], name="casal_data_inicio_idx"),
        ]
        # Evita casais duplicados
        unique_together = [("reprodutor_macho", "matriz_femea", "data_inicio")]

    def __str__(self):
        macho = self.reprodutor_macho.ave.codigo_interno if self.reprodutor_macho else "?"
        femea = self.matriz_femea.ave.codigo_interno if self.matriz_femea else "?"
        return f"Casal {macho} × {femea} ({self.get_status_display()})"

    def clean(self):
        """Validações de integridade."""
        from django.core.exceptions import ValidationError
        
        if not self.reprodutor_macho or self.reprodutor_macho.tipo != Reprodutor.TIPO_REPRODUTOR:
            raise ValidationError("Reprodutor deve ser macho")
        
        if not self.matriz_femea or self.matriz_femea.tipo != Reprodutor.TIPO_MATRIZ:
            raise ValidationError("Matriz deve ser fêmea")
        
        if self.reprodutor_macho.ave == self.matriz_femea.ave:
            raise ValidationError("Reprodutor e matriz devem ser aves diferentes")
        
        if self.data_fim and self.data_fim < self.data_inicio:
            raise ValidationError("Data de término não pode ser anterior à data de início")

    @property
    def duracao_reproducao(self):
        """Calcula duração em dias da reprodução (até agora ou até fim)."""
        from django.utils import timezone
        fim = self.data_fim or timezone.localdate()
        return (fim - self.data_inicio).days

    def get_filhotes_count(self):
        """Conta filhotes deste casal (baseado em lotes ou registros genéticos)."""
        if not self.reprodutor_macho or not self.matriz_femea:
            return 0
        from genetica.models import RegistroGenetico
        return RegistroGenetico.objects.filter(
            pai=self.reprodutor_macho.ave,
            mae=self.matriz_femea.ave
        ).count()
