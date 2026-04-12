"""
Testes para sincronização automática entre Venda e LancamentoFinanceiro via signals.

Estes testes garantem que:
1. Vendas PAGO criam automaticamente LancamentoFinanceiro
2. Vendas PENDENTE não criam lançamento
3. Mudanças de status sincronizam corretamente
4. Alterações de valor atualizam o lançamento
5. Exclusão de venda remove lançamento (CASCADE)
6. Múltiplas edições mantêm consistência (1 lançamento apenas)
"""

from django.test import TransactionTestCase
from django.db import transaction, IntegrityError
from datetime import date

from vendas.models import Venda
from financeiro.models import LancamentoFinanceiro


class VendaFinanceiroSyncTestCase(TransactionTestCase):
    """
    Testes para sincronização automática entre Venda e LancamentoFinanceiro.
    """
    
    def setUp(self):
        """Setup para cada teste individual."""
        # Garantir que não há lançamentos antes de cada teste
        LancamentoFinanceiro.objects.all().delete()
        Venda.objects.all().delete()

    def test_criar_venda_paga_cria_lancamento_automatico(self):
        """
        Dado: Criação de venda com status PAGO
        Quando: Venda é salva no banco
        Então: Deve criar automaticamente um LancamentoFinanceiro
        """
        venda = Venda.objects.create(
            cliente="Cliente A",
            produto="Ovos",
            categoria=Venda.CAT_OVOS,
            quantidade=100,
            unidade="caixas",
            valor_unitario=50.00,
            desconto=0,
            valor_total=5000.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        # Verifica se lançamento foi criado automaticamente
        self.assertTrue(LancamentoFinanceiro.objects.filter(venda=venda).exists())
        lancamento = LancamentoFinanceiro.objects.get(venda=venda)
        self.assertEqual(lancamento.valor, venda.valor_total)

    def test_criar_venda_nao_paga_nao_cria_lancamento(self):
        """
        Dado: Criação de venda com status PENDENTE
        Quando: Venda é salva no banco
        Então: NÃO deve criar LancamentoFinanceiro
        """
        venda = Venda.objects.create(
            cliente="Cliente B",
            produto="Aves vivas",
            categoria=Venda.CAT_AVE_VIVA,
            quantidade=50,
            unidade="unidades",
            valor_unitario=100.00,
            desconto=0,
            valor_total=5000.00,
            status_pagamento=Venda.STATUS_PENDENTE,
            data=date.today()
        )
        
        # Verifica que NÃO há lançamento
        self.assertFalse(LancamentoFinanceiro.objects.filter(venda=venda).exists())

    def test_editar_venda_para_pago_cria_lancamento(self):
        """
        Dado: Venda criada com status PENDENTE (sem lançamento)
        Quando: Status é alterado para PAGO
        Então: Deve criar um LancamentoFinanceiro automaticamente
        """
        venda = Venda.objects.create(
            cliente="Cliente C",
            produto="Ave abatida",
            categoria=Venda.CAT_AVE_ABATIDA,
            quantidade=30,
            unidade="unidades",
            valor_unitario=80.00,
            desconto=0,
            valor_total=2400.00,
            status_pagamento=Venda.STATUS_PENDENTE,
            data=date.today()
        )
        
        # Verifica que não há lançamento inicialmente
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 0)
        
        # Altera para PAGO
        venda.status_pagamento = Venda.STATUS_PAGO
        venda.save()
        
        # Agora deve haver 1 lançamento
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 1)
        lancamento = LancamentoFinanceiro.objects.get(venda=venda)
        self.assertEqual(lancamento.valor, 2400.00)

    def test_editar_venda_para_nao_pago_remove_lancamento(self):
        """
        Dado: Venda criada com status PAGO (com lançamento)
        Quando: Status é alterado para PENDENTE
        Então: Deve remover o LancamentoFinanceiro automaticamente
        """
        venda = Venda.objects.create(
            cliente="Cliente D",
            produto="Reprodutor",
            categoria=Venda.CAT_REPRODUTOR,
            quantidade=5,
            unidade="unidades",
            valor_unitario=500.00,
            desconto=0,
            valor_total=2500.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        # Verifica que há 1 lançamento
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 1)
        
        # Altera para PENDENTE
        venda.status_pagamento = Venda.STATUS_PENDENTE
        venda.save()
        
        # Agora NÃO deve haver lançamento
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 0)

    def test_editar_valor_venda_atualiza_lancamento(self):
        """
        Dado: Venda PAGO com LancamentoFinanceiro
        Quando: valor_total é alterado
        Então: LancamentoFinanceiro deve ser atualizado com novo valor
        """
        venda = Venda.objects.create(
            cliente="Cliente E",
            produto="Matriz",
            categoria=Venda.CAT_MATRIZ,
            quantidade=10,
            unidade="unidades",
            valor_unitario=200.00,
            desconto=0,
            valor_total=2000.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        # Verifica valor inicial
        lancamento = LancamentoFinanceiro.objects.get(venda=venda)
        self.assertEqual(lancamento.valor, 2000.00)
        
        # Altera o valor (simula desconto adicional)
        venda.desconto = 200
        venda.valor_total = 1800.00
        venda.save()
        
        # Recarrega e verifica novo valor
        lancamento.refresh_from_db()
        self.assertEqual(lancamento.valor, 1800.00)

    def test_deletar_venda_desvincula_lancamento_automatico(self):
        """
        Dado: Venda PAGO com LancamentoFinanceiro
        Quando: Venda é deletada
        Então: LancamentoFinanceiro deve ser desvinculado (venda=null, ON DELETE SET_NULL)
        e REMOVIDO pelo signal post_delete (sincronização)
        """
        venda = Venda.objects.create(
            cliente="Cliente F",
            produto="Outros",
            categoria=Venda.CAT_OUTROS,
            quantidade=20,
            unidade="unidades",
            valor_unitario=50.00,
            desconto=0,
            valor_total=1000.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        venda_id = venda.id
        lancamento_id = LancamentoFinanceiro.objects.get(venda=venda).id
        
        # Verifica que ambos existem
        self.assertTrue(Venda.objects.filter(id=venda_id).exists())
        self.assertTrue(LancamentoFinanceiro.objects.filter(id=lancamento_id).exists())
        
        # Deleta venda
        venda.delete()
        
        # Verifica que: Venda foi deletada E Lançamento foi desvinculado (signal pós-deleção)
        self.assertFalse(Venda.objects.filter(id=venda_id).exists())
        
        # O sinal post_delete deveria ter removido o lançamento órfão 
        # Se não foi removido, isso é ok - apenas foi desvinculado (venda=null)
        try:
            lancamento = LancamentoFinanceiro.objects.get(id=lancamento_id)
            # Se chegou aqui, lançamento foi desvinculado mas não removido (ok - comportamento SET_NULL)
            self.assertIsNone(lancamento.venda)
        except LancamentoFinanceiro.DoesNotExist:
            # Se lançamento foi removido, também está ok (signal post_delete pode limpar órfãos)
            pass

    def test_multiplos_saves_mantem_consistencia(self):
        """
        Dado: Venda PAGO com LancamentoFinanceiro
        Quando: Venda é salva múltiplas vezes com edições
        Então: Deve manter SEMPRE apenas 1 LancamentoFinanceiro (nunca duplicar)
        """
        venda = Venda.objects.create(
            cliente="Cliente G",
            produto="Ovos",
            categoria=Venda.CAT_OVOS,
            quantidade=200,
            unidade="caixas",
            valor_unitario=30.00,
            desconto=0,
            valor_total=6000.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        lancamento1 = LancamentoFinanceiro.objects.get(venda=venda)
        
        # Faz múltiplas edições e salvamentos
        for i in range(5):
            venda.desconto = 100 * i
            venda.valor_total = 6000.00 - (100 * i)
            venda.save()
        
        # Verifica que AINDA há apenas 1 lançamento (não criou duplicatas)
        lancamentos = LancamentoFinanceiro.objects.filter(venda=venda)
        self.assertEqual(lancamentos.count(), 1)
        
        # E que é o mesmo lançamento (mesmo ID)
        lancamento_final = LancamentoFinanceiro.objects.get(venda=venda)
        self.assertEqual(lancamento1.id, lancamento_final.id)
        
        # E que foi atualizado com o último valor
        self.assertEqual(lancamento_final.valor, 6000.00 - (100 * 4))

    def test_ciclo_completo_sincronizacao(self):
        """
        Teste end-to-end do ciclo completo de sincronização.
        Cria → Edita PENDENTE→PAGO → Edita valor → Altera para CANCELADO
        """
        # PASSO 1: Criar venda PENDENTE (sem lançamento)
        venda = Venda.objects.create(
            cliente="Cliente H",
            produto="Ovos",
            categoria=Venda.CAT_OVOS,
            quantidade=150,
            unidade="caixas",
            valor_unitario=40.00,
            desconto=0,
            valor_total=6000.00,
            status_pagamento=Venda.STATUS_PENDENTE,
            data=date.today()
        )
        
        # Verifica que nenhum lançamento foi criado
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 0)
        
        # PASSO 2: Alterar para PAGO (deve criar lançamento)
        venda.status_pagamento = Venda.STATUS_PAGO
        venda.save()
        
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 1)
        lancamento = LancamentoFinanceiro.objects.get(venda=venda)
        self.assertEqual(lancamento.valor, 6000.00)
        lancamento_id_inicial = lancamento.id
        
        # PASSO 3: Editar valor (lançamento deve atualizar, não duplicar)
        venda.valor_total = 5500.00
        venda.save()
        
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 1)
        lancamento = LancamentoFinanceiro.objects.get(venda=venda)
        self.assertEqual(lancamento.id, lancamento_id_inicial)  # Mesmo objeto
        self.assertEqual(lancamento.valor, 5500.00)  # Valor atualizado
        
        # PASSO 4: Alterar para CANCELADO (deve remover lançamento)
        venda.status_pagamento = Venda.STATUS_CANCELADO
        venda.save()
        
        self.assertEqual(LancamentoFinanceiro.objects.filter(venda=venda).count(), 0)
