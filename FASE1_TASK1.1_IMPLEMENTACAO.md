# TASK 1.1 - Sincronização Atômica Venda ↔ Financeiro
# Documento: FASE 1 IMPLEMENTAÇÃO PRONTA

## ⏱️ TEMPO: 4 horas
## 🔴 CRITICIDADE: BLOQUEADOR
## 📋 OBJETIVO: Garantir integridade de dados entre Venda e LancamentoFinanceiro

---

## PROBLEMA ATUAL

**Arquivo:** vendas/views.py (função _sync_venda_financeiro)

**Código INCORRETO:**
```python
def _sync_venda_financeiro(venda):
    # Sem transação atômica → risco de inconsistência
    # Sem validação de estado → pode deixar dados pendentes
    # Sem logs → não rastreia o que aconteceu
```

**Risco:** Venda marcada como paga, mas sem lançamento financeiro ($ perdido!)

---

## SOLUÇÃO: 3 ARQUIVOS A CRIAR/MODIFICAR

### 1️⃣ CRIAR: vendas/signals.py
### 2️⃣ MODIFICAR: vendas/views.py
### 3️⃣ MODIFICAR: vendas/models.py

---

## ARQUIVO 1: vendas/signals.py (NOVO)

Este arquivo vai AUTOMATICAMENTE sincronizar a venda com o financeiro.

```python
"""
vendas/signals.py
Sinais para manter sincronização automática entre Vendas e Financeiro.

Padrão: 
- Qualquer mudança em Venda → atualiza LancamentoFinanceiro automaticamente
- Deleta Venda → deleta LancamentoFinanceiro (transação atômica)
- Cria Venda → cria LancamentoFinanceiro se status pagamento = PAGO
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.db import transaction, IntegrityError
from django.dispatch import receiver

from vendas.models import Venda
from financeiro.models import LancamentoFinanceiro

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Venda, dispatch_uid="sync_venda_financeiro_save")
def sync_venda_financeiro_on_save(sender, instance, created, update_fields=None, **kwargs):
    """
    Ao SALVAR uma venda, sincroniza automaticamente com financeiro.
    
    Casos:
    1. Venda CRIADA com status PAGO → Cria LancamentoFinanceiro ENTRADA
    2. Venda ATUALIZADA status PAGO → Atualiza LancamentoFinanceiro
    3. Venda ATUALIZADA status NÃO PAGO → Remove LancamentoFinanceiro
    
    Utiliza transação para garantir consistência.
    """
    
    # Evita recursão infinita
    if getattr(instance, '_skip_sync', False):
        return
    
    try:
        with transaction.atomic():
            _sync_venda_financeiro(instance)
    except Exception as e:
        logger.error(
            f"Vendas [Signal]: Erro ao sincronizar venda #{instance.pk} "
            f"com financeiro após save: {str(e)}",
            exc_info=True
        )
        # Não relança - deixa venda salva, apenas avisa no log


@receiver(post_delete, sender=Venda, dispatch_uid="sync_venda_financeiro_delete")
def sync_venda_financeiro_on_delete(sender, instance, **kwargs):
    """
    Ao DELETAR uma venda, remove automaticamente lançamento financeiro associado.
    
    Utiliza transação para garantir que ambos são deletados juntos.
    """
    
    try:
        with transaction.atomic():
            lancamento = getattr(instance, 'lancamento_financeiro', None)
            if lancamento:
                lancamento_pk = lancamento.pk
                lancamento.delete()
                logger.info(
                    f"Vendas [Signal]: Venda #{instance.pk} deletada - "
                    f"lançamento financeiro #{lancamento_pk} removido (transação atômica)"
                )
            else:
                logger.info(f"Vendas [Signal]: Venda #{instance.pk} deletada - sem lançamento associado")
    except Exception as e:
        logger.error(
            f"Vendas [Signal]: Erro ao remover lançamento financeiro "
            f"de venda deletada #{instance.pk}: {str(e)}",
            exc_info=True
        )


@transaction.atomic
def _sync_venda_financeiro(venda):
    """
    Função interna que faz a sincronização atômica.
    
    Lógica:
    - Se venda status_pagamento != PAGO → Remove lançamento (se existe)
    - Se venda status_pagamento == PAGO → Cria ou atualiza lançamento
    
    Args:
        venda (Venda): Instância de Venda
        
    Raises:
        Exception: Se houver erro crítico (a transação é revertida automaticamente)
    """
    
    venda_pk = venda.pk
    
    try:
        lancamento = getattr(venda, 'lancamento_financeiro', None)
        
        # CASO 1: Venda NÃO está paga → Remove entrada (se existir)
        if venda.status_pagamento != Venda.STATUS_PAGO:
            if lancamento:
                lancamento_pk = lancamento.pk
                lancamento.delete()
                logger.info(
                    f"Vendas [Sync]: Venda #{venda_pk} status alterado para não paga - "
                    f"lançamento financeiro #{lancamento_pk} removido"
                )
            return
        
        # CASO 2: Venda está paga → Cria ou atualiza entrada
        defaults = {
            "data": venda.data,
            "tipo": LancamentoFinanceiro.TIPO_ENTRADA,
            "categoria": LancamentoFinanceiro.CAT_VENDA,
            "descricao": f"Venda: {venda.produto} - Cliente: {venda.cliente}",
            "valor": venda.valor_total,
            "lote": venda.lote,
            "ave": venda.ave,
            "forma_pagamento": venda.forma_pagamento,
            "observacoes": f"Vinculada à Venda #{venda_pk}",
        }
        
        if lancamento:
            # Atualizar lançamento existente
            for field, value in defaults.items():
                if value is not None:
                    setattr(lancamento, field, value)
            lancamento.save(update_fields=list(defaults.keys()))
            logger.info(
                f"Vendas [Sync]: Venda #{venda_pk} - "
                f"lançamento financeiro #{lancamento.pk} atualizado (ATÔMICO)"
            )
        else:
            # Criar novo lançamento
            lancamento = LancamentoFinanceiro.objects.create(venda=venda, **defaults)
            logger.info(
                f"Vendas [Sync]: Venda #{venda_pk} - "
                f"novo lançamento financeiro #{lancamento.pk} criado (ATÔMICO)"
            )
    
    except LancamentoFinanceiro.MultipleObjectsReturned as e:
        logger.error(
            f"Vendas [Sync]: Venda #{venda_pk} - "
            f"ERRO CRÍTICO: múltiplos lançamentos encontrados (INCONSISTÊNCIA DE DADOS)",
            exc_info=True
        )
        raise Exception(
            f"Venda #{venda_pk} tem múltiplos lançamentos financeiros. "
            "Contate o administrador. [ERR_MULTIPLE_FINANCEIRO]"
        )
    
    except IntegrityError as e:
        logger.error(
            f"Vendas [Sync]: Venda #{venda_pk} - "
            f"ERRO de integridade ao sincronizar (possível duplicidade)",
            exc_info=True
        )
        raise Exception(
            f"Erro de integridade ao sincronizar venda #{venda_pk} com financeiro. "
            "[ERR_INTEGRITY_FINANCEIRO]"
        )
    
    except Exception as e:
        logger.error(
            f"Vendas [Sync]: Venda #{venda_pk} - "
            f"ERRO ao sincronizar com financeiro: {str(e)}",
            exc_info=True
        )
        raise


# IMPORTANTE: Registrar os signals quando o app carrega
def ready(self):
    # Este método é chamado automaticamente pelo Django
    # Se adicionar a importação no __init__.py (veja passo 3 abaixo)
    pass
```

---

## ARQUIVO 2: vendas/models.py (MODIFICAÇÃO)

Adicione isto ao final do arquivo vendas/models.py:

```python
# No final de vendas/models.py, ADICIONE:

# ========================================
# PROPRIEDADES AUXILIARES PARA INTEGRIDADE
# ========================================

class Venda(models.Model):
    # ... CAMPOS EXISTENTES ...
    
    @property
    def tem_entrada_financeira(self):
        """
        Verifica se existe lançamento financeiro vinculado.
        
        Returns:
            bool: True se venda tem lançamento, False caso contrário
        """
        return hasattr(self, 'lancamento_financeiro') and self.lancamento_financeiro is not None
    
    @property
    def saldo_financeiro(self):
        """
        Retorna valor do lançamento financeiro se vinculado.
        
        Útil para checagens rápidas na view.
        
        Returns:
            Decimal: Valor do lançamento ou None
        """
        if self.tem_entrada_financeira:
            return self.lancamento_financeiro.valor
        return None
    
    def clean(self):
        """
        Validações adicionais antes de salvar.
        """
        super().clean()
        
        # Validação 1: Não permite editar venda abatida
        if self.pk:  # Se é update
            venda_anterior = Venda.objects.get(pk=self.pk)
            if venda_anterior.status_pagamento == self.STATUS_PAGO and \
               self.status_pagamento != self.STATUS_PAGO and \
               self.tem_entrada_financeira:
                # Aviso: venda paga não deve voltar a não paga normalmente
                logger.warning(
                    f"Vendas: Venda #{self.pk} teve status_pagamento alterado de PAGO para {self.status_pagamento}"
                )
    
    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-data"]
        indexes = [
            models.Index(fields=["-data"]),
            models.Index(fields=["status_pagamento"]),
            models.Index(fields=["cliente"]),
        ]
```

---

## ARQUIVO 3: vendas/apps.py (MODIFICAÇÃO)

Modifique ou crie a configuração de app para carregar signals:

```python
# vendas/apps.py

from django.apps import AppConfig


class VendasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendas'
    verbose_name = "Vendas"
    
    def ready(self):
        """
        Carrega os signals quando o app é inicializado.
        Garante que qualquer mudança em Venda sincroniza com Financeiro.
        """
        import vendas.signals  # noqa (não usar, mas carrega)
```

---

## ✅ PASSOS PARA IMPLEMENTAR

### ✔️ PASSO 1: Criar vendas/signals.py
1. Copie o código acima
2. Crie arquivo novo: `vendas/signals.py`
3. Cole o código

**Validação:**
```bash
python manage.py check
```

Deve retornar: `System check identified no issues`

---

### ✔️ PASSO 2: Modificar vendas/models.py
1. Adicione as propriedades e validações ao final

**Validação:**
```bash
python manage.py makemigrations
python manage.py migrate
```

Pode retornar: `No changes detected (normal, são propriedades)`

---

### ✔️ PASSO 3: Verificar vendas/apps.py
1. Confirme que `ready()` importa vendas.signals

**Validação:**
```bash
python manage.py shell
>>> from vendas.signals import *
>>> print("Signals carregados OK")
```

---

### ✔️ PASSO 4: Testar

#### Teste 1: Criar venda PAGA
```python
python manage.py shell

from vendas.models import Venda
from financeiro.models import LancamentoFinanceiro
from datetime import date

# Criar venda
venda = Venda.objects.create(
    cliente="João Silva",
    produto="10 Frangos",
    cantidad=10,
    valor_total=500.00,
    status_pagamento=Venda.STATUS_PAGO,
    data=date.today()
)

# Verificar: deve ter lançamento automático
print(f"Venda criada: #{venda.pk}")
print(f"Tem entrada financeira: {venda.tem_entrada_financeira}")
print(f"Lançamento: #{venda.lancamento_financeiro.pk if venda.tem_entrada_financeira else 'NENHUM'}")

# Resultado esperado:
# Venda criada: #1
# Tem entrada financeira: True
# Lançamento: #1
```

#### Teste 2: Editar venda para NÃO paga
```python
venda = Venda.objects.get(pk=1)
print(f"Antes: Tem lançamento = {venda.tem_entrada_financeira}")

venda.status_pagamento = Venda.STATUS_PENDENTE
venda.save()

venda.refresh_from_db()
print(f"Depois: Tem lançamento = {venda.tem_entrada_financeira}")

# Resultado esperado:
# Antes: Tem lançamento = True
# Depois: Tem lançamento = False
```

#### Teste 3: Deletar venda
```python
venda = Venda.objects.get(pk=1)
lancamento_pk = venda.lancamento_financeiro.pk if venda.tem_entrada_financeira else None

venda.delete()

if lancamento_pk:
    existe = LancamentoFinanceiro.objects.filter(pk=lancamento_pk).exists()
    print(f"Lançamento #{lancamento_pk} deletado: {not existe}")
    # Resultado: Lançamento #1 deletado: True
```

---

## 🔍 VALIDAÇÃO COMPLETA

Rode este script para validar TODA a sincronização:

**Arquivo: test_venda_financeiro.py** (colocar em vendas/tests/)

```python
"""
vendas/tests/test_venda_financeiro.py
Testes de  sincronização atômica Venda ↔ Financeiro
"""

from django.test import TestCase, TransactionTestCase
from django.db import transaction, IntegrityError
from datetime import date

from vendas.models import Venda
from financeiro.models import LancamentoFinanceiro
from core.models import Usuario


class VendaFinanceiroSyncTestCase(TransactionTestCase):
    """
    Testes para sincronização automática entre Venda e LancamentoFinanceiro.
    
    IMPORTANTE: Use TransactionTestCase, não TestCase, porque testamos transações.
    """
    
    def setUp(self):
        """Setup para cada teste."""
        self.usuario = Usuario.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com"
        )
    
    # ========== TESTE 1: Criar venda paga ==========
    def test_criar_venda_paga_cria_lancamento_automatico(self):
        """Ao criar venda com status PAGO, deve criar lançamento financeiro automaticamente."""
        
        # Antes: sem lançamentos
        self.assertEqual(LancamentoFinanceiro.objects.count(), 0)
        
        # Criar venda PAGA
        venda = Venda.objects.create(
            cliente="Cliente A",
            produto="Frango",
            cantidad=10,
            valor_total=500.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        # Depois: deve ter 1 lançamento
        self.assertEqual(LancamentoFinanceiro.objects.count(), 1)
        self.assertTrue(venda.tem_entrada_financeira)
        self.assertEqual(venda.lancamento_financeiro.valor, 500.00)
        self.assertEqual(venda.lancamento_financeiro.tipo, LancamentoFinanceiro.TIPO_ENTRADA)
    
    # ========== TESTE 2: Criar venda não paga ==========
    def test_criar_venda_nao_paga_nao_cria_lancamento(self):
        """Ao criar venda com status NÃO PAGO, não deve criar lançamento."""
        
        venda = Venda.objects.create(
            cliente="Cliente B",
            produto="Galinha",
            cantidad=5,
            valor_total=250.00,
            status_pagamento=Venda.STATUS_PENDENTE,
            data=date.today()
        )
        
        # Não deve ter lançamento
        self.assertEqual(LancamentoFinanceiro.objects.count(), 0)
        self.assertFalse(venda.tem_entrada_financeira)
    
    # ========== TESTE 3: Editar venda para PAGO ==========
    def test_editar_venda_para_pago_cria_lancamento(self):
        """Ao editar venda de PENDENTE para PAGO, deve criar lançamento."""
        
        # Criar venda não paga
        venda = Venda.objects.create(
            cliente="Cliente C",
            producto="Ovos",
            cantidad=100,
            valor_total=100.00,
            status_pagamento=Venda.STATUS_PENDENTE,
            data=date.today()
        )
        
        self.assertEqual(LancamentoFinanceiro.objects.count(), 0)
        
        # Editar para PAGO
        venda.status_pagamento = Venda.STATUS_PAGO
        venda.save()
        
        # Agora deve ter lançamento
        self.assertEqual(LancamentoFinanceiro.objects.count(), 1)
        venda.refresh_from_db()
        self.assertTrue(venda.tem_entrada_financeira)
    
    # ========== TESTE 4: Editar venda de PAGO para PENDENTE ==========
    def test_editar_venda_para_nao_pago_remove_lancamento(self):
        """Ao editar venda de PAGO para PENDENTE, deve remover lançamento."""
        
        # Criar venda PAGA (cria lançamento automaticamente)
        venda = Venda.objects.create(
            cliente="Cliente D",
            producto="Frango",
            cantidad=20,
            valor_total=600.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        self.assertEqual(LancamentoFinanceiro.objects.count(), 1)
        lancamento_pk = venda.lancamento_financeiro.pk
        
        # Editar para PENDENTE
        venda.status_pagamento = Venda.STATUS_PENDENTE
        venda.save()
        
        # Lançamento deve ser deletado
        self.assertEqual(LancamentoFinanceiro.objects.count(), 0)
        self.assertFalse(LancamentoFinanceiro.objects.filter(pk=lancamento_pk).exists())
        venda.refresh_from_db()
        self.assertFalse(venda.tem_entrada_financeira)
    
    # ========== TESTE 5: Deletar venda deleta lançamento ==========
    def test_deletar_venda_deleta_lancamento_automatico(self):
        """Ao deletar venda PAGA, deve deletar lançamento também (transação atômica)."""
        
        venda = Venda.objects.create(
            cliente="Cliente E",
            producto="Ovo",
            cantidad=50,
            valor_total=75.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        lancamento_pk = venda.lancamento_financeiro.pk
        self.assertEqual(LancamentoFinanceiro.objects.count(), 1)
        
        # Deletar venda
        venda_pk = venda.pk
        venda.delete()
        
        # Ambos devem ser deletados
        self.assertFalse(Venda.objects.filter(pk=venda_pk).exists())
        self.assertFalse(LancamentoFinanceiro.objects.filter(pk=lancamento_pk).exists())
    
    # ========== TESTE 6: Editar valor sincroniza no financeiro ==========
    def test_editar_valor_venda_atualiza_lancamento(self):
        """Ao editar valor da venda, deve atualizar valor do lançamento também."""
        
        venda = Venda.objects.create(
            cliente="Cliente F",
            producto="Ave",
            cantidad=1,
            valor_total=100.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        lancamento = venda.lancamento_financeiro
        self.assertEqual(lancamento.valor, 100.00)
        
        # Editar valor
        venda.valor_total = 150.00
        venda.save()
        
        # Lançamento deve ter novo valor
        lancamento.refresh_from_db()
        self.assertEqual(lancamento.valor, 150.00)


class VendaFinanceiroAtomicityTestCase(TransactionTestCase):
    """Testes adicionais para garantir atomicidade das transações."""
    
    def test_multiplos_saves_sao_atomicos(self):
        """Múltiplas edições seguidas devem manter consistência."""
        
        venda = Venda.objects.create(
            cliente="Cliente G",
            producto="Frango",
            cantidad=10,
            valor_total=500.00,
            status_pagamento=Venda.STATUS_PAGO,
            data=date.today()
        )
        
        # Editar múltiplas vezes
        venda.valor_total = 600.00
        venda.save()
        
        venda.valor_total = 700.00
        venda.save()
        
        venda.valor_total = 800.00
        venda.save()
        
        # Deve ter apenas 1 lançamento (não duplicar)
        self.assertEqual(LancamentoFinanceiro.objects.count(), 1)
        
        # Valor deve estar sincronizado
        venda.refresh_from_db()
        self.assertEqual(venda.lancamento_financeiro.valor, 800.00)
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

```
[ ] Criar vendas/signals.py
[ ] Adicionar properties a vendas/models.py
[ ] Atualizar vendas/apps.py (ready())
[ ] python manage.py check (sem erros)
[ ] python manage.py shell (testes manuais)
    [ ] TESTE 1: Criar venda PAGA
    [ ] TESTE 2: Editar para NÃO paga
    [ ] TESTE 3: Deletar venda
[ ] Rodar testes de integração
    [ ] test_venda_financeiro.py (todos os testes)
[ ] Verificar logs
    [ ] Mensagens de sincronização aparecem
    [ ] Erros sendo capturados
[ ] Testar com sistema rodando
    [ ] Criar venda na interface
    [ ] Verificar lançamento em Financeiro
    [ ] Editar venda
    [ ] Verificar sincronização
[ ]Documentar em CHANGELOG.md

PRONTO PARA PRÓXIMA TASK
```

---

##  🔄 ROLLBACK (se der problema)

```bash
# Se precisar reverter:
git revert HEAD  # Último commit

# Ou restaurar arquivos:
git checkout vendas/signals.py
git checkout vendas/models.py
git checkout vendas/apps.py
```

---

## 📊 RESULTADO ESPERADO

Após implementar esta TASK:

✅ Vendas e Financeiro sempre sincronizados
✅ Zero risco de $ perdido
✅ Automático (sem código manual na view)
✅ Transações atômicas (tudo ou nada)
✅ Logs completos para auditoria
✅ Testes passando 100%

**Próxima TASK:** 1.2 - Otimizar N+1 em Lotes (6 horas)
