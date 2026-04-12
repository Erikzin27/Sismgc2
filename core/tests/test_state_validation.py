"""
Testes para validação de máquina de estados (TASK 1.3)

Garante que transições inválidas entre estados são impedidas.
Protege integridade de dados e fluxos de negócio.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date

from vendas.models import Venda
from aves.models import Ave
from lotes.models import Lote
from linhagens.models import Linhagem


# ============================================================================
# TESTES: Venda - State Validation
# ============================================================================

class VendaStateValidationTestCase(TestCase):
    """Testes para transições de estado de Venda.status_pagamento"""
    
    def setUp(self):
        """Cria venda de teste"""
        self.venda = Venda.objects.create(
            data=date.today(),
            cliente="Cliente Test",
            produto="Teste",
            categoria=Venda.CAT_OVOS,
            quantidade=100,
            valor_unitario=50,
            valor_total=5000,
            status_pagamento=Venda.STATUS_PENDENTE,
        )
    
    def test_pendente_para_pago_valido(self):
        """PENDENTE → PAGO: Deve ser válido"""
        self.venda.status_pagamento = Venda.STATUS_PAGO
        self.venda.full_clean()  # Não deve lançar exceção
        self.venda.save()
        self.assertEqual(self.venda.status_pagamento, Venda.STATUS_PAGO)
    
    def test_pendente_para_cancelado_valido(self):
        """PENDENTE → CANCELADO: Deve ser válido"""
        self.venda.status_pagamento = Venda.STATUS_CANCELADO
        self.venda.full_clean()
        self.venda.save()
        self.assertEqual(self.venda.status_pagamento, Venda.STATUS_CANCELADO)
    
    def test_pago_para_pendente_valido(self):
        """PAGO → PENDENTE: Deve ser válido (correção)"""
        self.venda.status_pagamento = Venda.STATUS_PAGO
        self.venda.save()
        
        self.venda.status_pagamento = Venda.STATUS_PENDENTE
        self.venda.full_clean()
        self.venda.save()
        self.assertEqual(self.venda.status_pagamento, Venda.STATUS_PENDENTE)
    
    def test_pago_para_cancelado_valido(self):
        """PAGO → CANCELADO: Deve ser válido"""
        self.venda.status_pagamento = Venda.STATUS_PAGO
        self.venda.save()
        
        self.venda.status_pagamento = Venda.STATUS_CANCELADO
        self.venda.full_clean()
        self.venda.save()
        self.assertEqual(self.venda.status_pagamento, Venda.STATUS_CANCELADO)
    
    def test_cancelado_invalido(self):
        """CANCELADO: Deve ser estado final (sem transições)"""
        self.venda.status_pagamento = Venda.STATUS_CANCELADO
        self.venda.save()
        
        # Tentar voltar para PENDENTE (inválido)
        self.venda.status_pagamento = Venda.STATUS_PENDENTE
        with self.assertRaises(ValidationError):
            self.venda.full_clean()
    
    def test_cancelado_para_pago_invalido(self):
        """CANCELADO → PAGO: Deve ser inválido"""
        self.venda.status_pagamento = Venda.STATUS_CANCELADO
        self.venda.save()
        
        self.venda.status_pagamento = Venda.STATUS_PAGO
        with self.assertRaises(ValidationError):
            self.venda.full_clean()
    
    def test_mesmo_estado_valido(self):
        """Transição para mesmo estado: Deve ser válida"""
        self.venda.status_pagamento = Venda.STATUS_PENDENTE
        self.venda.full_clean()
        self.venda.save()
        # Não deve lançar erro


# ============================================================================
# TESTES: Ave - State Validation
# ============================================================================

class AveStateValidationTestCase(TestCase):
    """Testes para transições de estado de Ave.status"""
    
    def setUp(self):
        """Cria ave de teste"""
        linhagem = Linhagem.objects.create(nome="Linhagem Test")
        self.ave = Ave.objects.create(
            codigo_interno="AVE001",
            identificacao="001",
            sexo=Ave.SEXO_FEMEA,
            finalidade=Ave.FINALIDADE_POSTURA,
            linhagem=linhagem,
            status=Ave.STATUS_VIVA,
        )
    
    def test_viva_para_vendida_valido(self):
        """VIVA → VENDIDA: Deve ser válido"""
        self.ave.status = Ave.STATUS_VENDIDA
        self.ave.full_clean()
        self.ave.save()
        self.assertEqual(self.ave.status, Ave.STATUS_VENDIDA)
    
    def test_viva_para_morta_valido(self):
        """VIVA → MORTA: Deve ser válido"""
        self.ave.status = Ave.STATUS_MORTA
        self.ave.full_clean()
        self.ave.save()
        self.assertEqual(self.ave.status, Ave.STATUS_MORTA)
    
    def test_viva_para_abatida_valido(self):
        """VIVA → ABATIDA: Deve ser válido"""
        self.ave.status = Ave.STATUS_ABATIDA
        self.ave.full_clean()
        self.ave.save()
        self.assertEqual(self.ave.status, Ave.STATUS_ABATIDA)
    
    def test_vendida_final_invalido(self):
        """VENDIDA: Deve ser estado final"""
        self.ave.status = Ave.STATUS_VENDIDA
        self.ave.save()
        
        # Tentar voltar para VIVA (inválido)
        self.ave.status = Ave.STATUS_VIVA
        with self.assertRaises(ValidationError):
            self.ave.full_clean()
    
    def test_morta_final_invalido(self):
        """MORTA: Deve ser estado final"""
        self.ave.status = Ave.STATUS_MORTA
        self.ave.save()
        
        # Tentar mudar para outro estado (inválido)
        self.ave.status = Ave.STATUS_VENDIDA
        with self.assertRaises(ValidationError):
            self.ave.full_clean()
    
    def test_abatida_final_invalido(self):
        """ABATIDA: Deve ser estado final"""
        self.ave.status = Ave.STATUS_ABATIDA
        self.ave.save()
        
        # Tentar mudar para outro estado (inválido)
        self.ave.status = Ave.STATUS_VIVA
        with self.assertRaises(ValidationError):
            self.ave.full_clean()


# ============================================================================
# TESTES: Lote - State Validation
# ============================================================================

class LoteStateValidationTestCase(TestCase):
    """Testes para transições de estado de Lote.status"""
    
    def setUp(self):
        """Cria lote de teste"""
        self.lote = Lote.objects.create(
            codigo="LOTE001",
            nome="Lote Test",
            data_criacao=date.today(),
            finalidade="postura",
            quantidade_inicial=100,
            status=Lote.STATUS_ATIVO,
        )
    
    def test_ativo_para_encerrado_valido(self):
        """ATIVO → ENCERRADO: Deve ser válido"""
        self.lote.status = Lote.STATUS_ENCERRADO
        self.lote.full_clean()
        self.lote.save()
        self.assertEqual(self.lote.status, Lote.STATUS_ENCERRADO)
    
    def test_encerrado_final_invalido(self):
        """ENCERRADO: Deve ser estado final"""
        self.lote.status = Lote.STATUS_ENCERRADO
        self.lote.save()
        
        # Tentar voltar para ATIVO (inválido)
        self.lote.status = Lote.STATUS_ATIVO
        with self.assertRaises(ValidationError):
            self.lote.full_clean()

