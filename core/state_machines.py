"""
State Machine Validation Mixin

Previne transições de estado inválidas em modelos Django.
Define máquinas de estado permitidas e valida transições antes de salvar.
"""

from django.core.exceptions import ValidationError


class StateTransitionMixin:
    """
    Mixin que implementa validação de máquina de estados.
    
    Modelos devem definir:
    - STATE_FIELD: nome do campo de estado (ex: 'status', 'status_pagamento')
    - STATE_TRANSITIONS: dict com transições permitidas
    
    Exemplo:
        STATE_FIELD = 'status'
        STATE_TRANSITIONS = {
            'ativo': ['encerrado'],  # ATIVO → ENCERRADO
            'encerrado': [],  # Sem transições (estado final)
        }
    """
    
    STATE_FIELD = None
    STATE_TRANSITIONS = {}
    
    def get_state_field_name(self):
        """Retorna o nome do campo de estado"""
        if self.STATE_FIELD is None:
            raise NotImplementedError(f"{self.__class__.__name__} deve definir STATE_FIELD")
        return self.STATE_FIELD
    
    def get_state_transitions(self):
        """Retorna mapa de transições permitidas"""
        if not self.STATE_TRANSITIONS:
            raise NotImplementedError(f"{self.__class__.__name__} deve definir STATE_TRANSITIONS")
        return self.STATE_TRANSITIONS
    
    def get_current_state(self):
        """Obtém estado atual"""
        return getattr(self, self.get_state_field_name())
    
    def get_previous_state(self):
        """Obtém estado anterior (do banco)"""
        if not self.pk:
            return None  # Novo objeto
        
        model_class = self.__class__
        try:
            db_instance = model_class.objects.get(pk=self.pk)
            return getattr(db_instance, self.get_state_field_name())
        except model_class.DoesNotExist:
            return None
    
    def is_valid_transition(self, from_state, to_state):
        """Verifica se transição é válida"""
        if from_state is None:
            # Novo objeto - sempre válido
            return True
        
        if from_state == to_state:
            # Mesmo estado - sempre válido
            return True
        
        transitions = self.get_state_transitions()
        if from_state not in transitions:
            return False
        
        allowed_states = transitions[from_state]
        return to_state in allowed_states
    
    def validate_state_transition(self):
        """
        Valida transição de estado.
        Chamado automaticamente em clean().
        """
        state_field = self.get_state_field_name()
        current_state = self.get_current_state()
        previous_state = self.get_previous_state()
        
        if not self.is_valid_transition(previous_state, current_state):
            transitions = self.get_state_transitions()
            allowed = transitions.get(previous_state, [])
            raise ValidationError(
                f"Transição inválida de estado: {previous_state} → {current_state}. "
                f"Transições permitidas: {previous_state} → {allowed}"
            )
    
    def clean(self):
        """Valida antes de salvar"""
        super().clean()
        self.validate_state_transition()
    
    def save(self, *args, **kwargs):
        """Valida antes de salvar"""
        self.full_clean()
        super().save(*args, **kwargs)


# ============================================================================
# Estado Machines Específicas por Modelo
# ============================================================================

class LoteStateMachine(StateTransitionMixin):
    """Máquina de estados para Lote"""
    
    STATE_FIELD = 'status'
    STATE_TRANSITIONS = {
        'ativo': ['encerrado'],  # Pode encerrar
        'encerrado': [],  # Estado final
    }


class LoteReproducaoStateMachine(StateTransitionMixin):
    """Máquina de estados para reprodução (Lote.status_reprodutivo)"""
    
    STATE_FIELD = 'status_reprodutivo'
    STATE_TRANSITIONS = {
        'ativo': ['pausado', 'encerrado'],  # Pausar ou encerrar
        'pausado': ['ativo', 'encerrado'],  # Retomar ou encerrar
        'encerrado': [],  # Estado final
    }
    
    def validate_state_transition(self):
        """Override: apenas valida se reprodutivo=True"""
        if not getattr(self, 'reprodutivo', False):
            # Se não reprodutivo, não valida (status_reprodutivo deve estar vazio)
            return
        super().validate_state_transition()


class AveStateMachine(StateTransitionMixin):
    """Máquina de estados para Ave"""
    
    STATE_FIELD = 'status'
    STATE_TRANSITIONS = {
        'viva': ['vendida', 'morta', 'abatida'],  # Pode sair de viva
        'vendida': [],  # Estado final
        'morta': [],  # Estado final
        'abatida': [],  # Estado final
    }


class VendaPaymentStateMachine(StateTransitionMixin):
    """Máquina de estados para status de pagamento de Venda"""
    
    STATE_FIELD = 'status_pagamento'
    STATE_TRANSITIONS = {
        'pendente': ['pago', 'cancelado'],  # Pode pagar ou cancelar
        'pago': ['pendente', 'cancelado'],  # Pode reverter para pendente (correção) ou cancelar
        'cancelado': [],  # Estado final
    }


class AplicacaoVacinaStateMachine(StateTransitionMixin):
    """Máquina de estados para AplicacaoVacina"""
    
    STATE_FIELD = 'status'
    STATE_TRANSITIONS = {
        'pendente': ['aplicada', 'cancelada'],  # Pode aplicar ou cancelar
        'aplicada': [],  # Estado final
        'cancelada': [],  # Estado final
    }


class TratamentoStateMachine(StateTransitionMixin):
    """Máquina de estados para Tratamento"""
    
    STATE_FIELD = 'status'
    STATE_TRANSITIONS = {
        'ativo': ['finalizado', 'cancelado'],  # Pode finalizar ou cancelar
        'finalizado': [],  # Estado final
        'cancelado': [],  # Estado final
    }
